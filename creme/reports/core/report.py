# -*- coding: utf-8 -*-

################################################################################
#    Creme is a free/open-source Customer Relationship Management software
#    Copyright (C) 2013-2015  Hybird
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
################################################################################

import logging

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import ManyToManyField, ForeignKey, FieldDoesNotExist
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _

from creme.creme_core.auth.entity_credentials import EntityCredentials
from creme.creme_core.gui.field_printers import field_printers_registry
from creme.creme_core.models import CremeEntity, RelationType, CustomField
from creme.creme_core.utils.meta import FieldInfo # get_related_field

from ..constants import (RFT_FUNCTION, RFT_RELATION, RFT_FIELD, RFT_CUSTOM,
        RFT_AGG_FIELD, RFT_AGG_CUSTOM, RFT_RELATED)
from ..report_aggregation_registry import field_aggregation_registry


logger = logging.getLogger(__name__)


class ReportHandRegistry(object):
    __slots__ = ('_hands', )

    def __init__(self):
        self._hands = {}

    def __call__(self, hand_id):
        assert hand_id not in self._hands, 'ID collision'

        def _aux(cls):
            self._hands[hand_id] = cls
            cls.hand_id = hand_id
            return cls

        return _aux

    def __getitem__(self, i):
        return self._hands[i]

    def __iter__(self):
        return iter(self._hands)

    def get(self, i):
        return self._hands.get(i)


REPORT_HANDS_MAP = ReportHandRegistry()


class ReportHand(object):
    "Class that computes values of a report column"
    verbose_name = 'OVERLOADME'

    class ValueError(Exception):
        pass

    def __init__(self, report_field, title, support_subreport=False):
        self._report_field = report_field
        self._title = title
        self._support_subreport = support_subreport

    def _generate_flattened_report(self, entities, user, scope):
        columns = self._report_field.sub_report.columns

        return u', '.join('/'.join(u"%s: %s" % (column.title, column.get_value(entity, user, scope))
                                        for column in columns
                                  ) for entity in entities
                         )

    #TODO: scope ??
    def _get_related_instances(self, entity, user):
        raise NotImplementedError

    def _get_filtered_related_entities(self, entity, user):
        related_entities = EntityCredentials.filter(user, self._get_related_instances(entity, user))
        report = self._report_field.sub_report

        if report.filter is not None:
            related_entities = report.filter.filter(related_entities)

        return related_entities

    def _get_value(self, entity, user, scope):
        # we are not building 'self._get_value' in __init__() because the
        # report_field.selected can change after the Hand building
        if self._support_subreport:
            report_field = self._report_field

            if report_field.sub_report:
                get_value = self._get_value_extended_subreport if report_field.selected else \
                            self._get_value_flattened_subreport
            else:
                get_value = self._get_value_no_subreport
        else:
            get_value = self._get_value_single

        self._get_value = get_value #cache

        return get_value(entity, user, scope)

    def _get_value_extended_subreport(self, entity, user, scope):
        """Used as _get_value() method by subclasses which manage
        sub-reports (extended sub-report case).
        """
        related_entities = self._get_filtered_related_entities(entity, user)
        gen_values = self._handle_report_values

        #"(None,)" : even if sub-scope if empty, with must generate empty columns for this line
        return [gen_values(e, user, related_entities) for e in related_entities or (None,)]

    def _get_value_flattened_subreport(self, entity, user, scope):
        """Used as _get_value() method by subclasses which manage
        sub-reports (flattened sub-report case).
        """
        return self._generate_flattened_report(self._get_filtered_related_entities(entity, user), user, scope)

    def _get_value_no_subreport(self, entity, user, scope):
        """Used as _get_value() method by subclasses which manage
        sub-reports (no sub-report case).
        """
        qs = self._get_related_instances(entity, user)
        extract = self._related_model_value_extractor

        if issubclass(qs.model, CremeEntity):
            qs = EntityCredentials.filter(user, qs)

        return u', '.join(unicode(extract(instance)) for instance in qs)

    def _get_value_single(self, entity, user, scope):
        """Used as _get_value() method by subclasses which does not manage
        sub-reports.
        """
        return settings.HIDDEN_VALUE if not user.has_perm_to_view(entity) else \
               self._get_value_single_on_allowed(entity, user, scope)

    def _get_value_single_on_allowed(self, entity, user, scope):
        "Overload this in sub-class when you compute the hand value (entity is viewable)"
        return

    def _handle_report_values(self, entity, user, scope):
        "@param entity CremeEntity instance, or None"
        return [rfield.get_value(entity, user, scope) for rfield in self._report_field.sub_report.columns]

    def _related_model_value_extractor(self, instance):
        return instance

    def get_linkable_ctypes(self):
        """Return the ContentType that are compatique, in order to link a subreport.
        @return A sequence of ContentTypes instances, or None (that means "can not link").
                An empty sequence means "All kind of CremeEntities are linkable"
        """
        return None

    def get_value(self, entity, user, scope):
        """Extract the value from entity for a Report cell.
        @param entity CremeEntity instance.
        @param user User instance ; used to compute credentials.
        @param scope QuerySet where 'entity' it comming from ; used by aggregates.
        """
        value = None

        if entity is None: #eg: a FK column was NULL, or the instance did not pass a filter
            if self._report_field.selected: #selected=True => self._report_field.sub_report is not None
                value = [self._handle_report_values(None, user, scope)]
        else:
            value = self._get_value(entity, user, scope)

        return u'' if value is None else value

    @property
    def hidden(self):
        "See FieldsConfig"
        return False

    @property
    def title(self):
        return self._title

    #def to_entity_cell(self):
        #"@return An equivalent EntityCell"
        #return None #todo: avoid None


@REPORT_HANDS_MAP(RFT_FIELD)
class RHRegularField(ReportHand):
    verbose_name = _(u'Regular field')

    _field_info = None  # Set by __new__()

    def __new__(cls, report_field):
        try:
            field_info = FieldInfo(report_field.model, report_field.name)
        except FieldDoesNotExist:
            raise ReportHand.ValueError('Invalid field: "%s" (does not exist)' % report_field.name)

        # if len(field_info) > 1 and isinstance(field_info[1], (ForeignKey, ManyToManyField)):
        #      raise ReportHand.ValueError('Invalid field: "%s"' % report_field.name)
        info_length = len(field_info)
        if info_length > 1:
            if info_length > 2:
                raise ReportHand.ValueError('Invalid field: "%s" (too deep)' % report_field.name)

            second_part = field_info[1]

            if (isinstance(second_part, (ForeignKey, ManyToManyField)) and
               issubclass(second_part.rel.to, CremeEntity)):
                raise ReportHand.ValueError('Invalid field: "%s" (no entity at depth=1)' % report_field.name)

        first_part = field_info[0]
        klass = RHForeignKey if isinstance(first_part, ForeignKey) else \
                RHManyToManyField if isinstance(first_part, ManyToManyField) else \
                RHRegularField

        instance = ReportHand.__new__(klass)
        instance._field_info = field_info

        return instance

    def __init__(self, report_field, support_subreport=False, title=None):
        model = report_field.model
        super(RHRegularField, self).__init__(report_field,
                                             title=title or self._field_info.verbose_name,
                                             support_subreport=support_subreport,
                                            )

        # TODO: FieldInfo is used by build_field_printer do the same work: can we factorise this ??
        self._printer = field_printers_registry.build_field_printer(model,
                                                                    report_field.name,
                                                                    output='csv',
                                                                   )

    def _get_value_single_on_allowed(self, entity, user, scope):
        return self._printer(entity, user)

    @property
    def field_info(self):
        return self._field_info

    @cached_property
    def hidden(self):
        rfield = self._report_field
        return rfield.report._fields_configs.is_fieldinfo_hidden(rfield.model,
                                                                 self._field_info,
                                                                )


class RHForeignKey(RHRegularField):
    def __init__(self, report_field):
        field_info = self._field_info
        fk_field = field_info[0]
        self._fk_attr_name = fk_field.get_attname()
        fk_model = fk_field.rel.to
        self._linked2entity = issubclass(fk_model, CremeEntity)
        qs = fk_model.objects.all()
        sub_report = report_field.sub_report

        if sub_report:
            efilter = sub_report.filter
            if efilter:
                qs = efilter.filter(qs)
        else:
            # Small optimization: only used by _get_value_no_subreport()
            if len(field_info) > 1:
                # attr_name = field_info[1].name
                # self._value_extractor = lambda fk_instance: getattr(fk_instance, attr_name, None)

                self._value_extractor = field_printers_registry.build_field_printer(
                                                        field_info[0].rel.to,
                                                        field_info[1].name,
                                                        output='csv',
                                                    )
            else:
                # self._value_extractor = unicode
                self._value_extractor = lambda fk_instance, user: unicode(fk_instance)

        self._qs = qs
        super(RHForeignKey, self).__init__(report_field,
                                           support_subreport=True,
                                           title=unicode(fk_field.verbose_name) if sub_report else None,
                                          )

    # NB: cannot rename to _get_related_instances() because forbidden entities are filtered instead of outputting '??'
    def _get_fk_instance(self, entity):
        try:
            entity = self._qs.get(pk=getattr(entity, self._fk_attr_name))
        except ObjectDoesNotExist:
            entity = None

        return entity

    def _get_value_flattened_subreport(self, entity, user, scope):
        fk_entity = self._get_fk_instance(entity)

        if fk_entity is not None: #TODO: test
            return self._generate_flattened_report((fk_entity,), user, scope)

    def _get_value_extended_subreport(self, entity, user, scope):
        return [self._handle_report_values(self._get_fk_instance(entity), user, scope)]

    def _get_value_no_subreport(self, entity, user, scope):
        fk_instance = self._get_fk_instance(entity)

        if fk_instance is not None:
            if self._linked2entity and not user.has_perm_to_view(fk_instance):
                return settings.HIDDEN_VALUE

            # return self._value_extractor(fk_instance)
            return self._value_extractor(fk_instance, user)

    def get_linkable_ctypes(self):
        return (ContentType.objects.get_for_model(self._qs.model),) \
               if self._linked2entity else None

    @property
    def linked2entity(self):
        return self._linked2entity


class RHManyToManyField(RHRegularField):
    def __init__(self, report_field):
        super(RHManyToManyField, self).__init__(report_field, support_subreport=True)
#        self._m2m_attr_name, sep, attr_name = report_field.name.partition('__')

#        self._related_model_value_extractor = \
#            (lambda instance: getattr(instance, attr_name, None) or u'') if attr_name else \
#            unicode

        field_info = self._field_info

        if len(field_info) > 1:
            attr_name = self._field_info[1].name
            # TODO: move "or u''" in base class ??
            self._related_model_value_extractor = \
                lambda instance: getattr(instance, attr_name, None) or u''
        else:
            self._related_model_value_extractor = unicode

    def _get_related_instances(self, entity, user):
#        return getattr(entity, self._m2m_attr_name).all()
        return getattr(entity, self._field_info[0].name).all()

    def get_linkable_ctypes(self):
#        m2m_model = self._report_field.model._meta.get_field(self._m2m_attr_name).rel.to
        m2m_model = self._field_info[0].rel.to

        return (ContentType.objects.get_for_model(m2m_model),) \
               if issubclass(m2m_model, CremeEntity) else None


@REPORT_HANDS_MAP(RFT_CUSTOM)
class RHCustomField(ReportHand):
    verbose_name = _(u'Custom field')

    def __init__(self, report_field):
        try:
            self._cfield = cf = CustomField.objects.get(id=report_field.name)
        except CustomField.DoesNotExist:
            raise ReportHand.ValueError('Invalid custom field: "%s"' % report_field.name)

        super(RHCustomField, self).__init__(report_field, title=cf.name)

    def _get_value_single_on_allowed(self, entity, user, scope):
        cvalue = entity.get_custom_value(self._cfield)
        return unicode(cvalue.value) if cvalue else u''


@REPORT_HANDS_MAP(RFT_RELATION)
class RHRelation(ReportHand):
    verbose_name = _(u'Relationship')

    def __init__(self, report_field):
        rtype_id = report_field.name

        try:
            self._rtype = rtype = RelationType.objects.get(id=rtype_id)
        except RelationType.DoesNotExist:
            raise ReportHand.ValueError('Invalid relation type: "%s"' % rtype_id)

        if report_field.sub_report:
            self._related_model = report_field.sub_report.ct.model_class()

        super(RHRelation, self).__init__(report_field,
                                         title=unicode(rtype.predicate),
                                         support_subreport=True,
                                        )

    def _get_related_instances(self, entity, user):
        return self._related_model.objects.filter(relations__type=self._rtype.symmetric_type,
                                                  relations__object_entity=entity.id,
                                                 )

    # TODO: add a feature in base class to retrieved efficently real entities ??
    # TODO: extract algorithm that retrieve efficently real entity from CremeEntity.get_related_entities()
    def _get_value_no_subreport(self, entity, user, scope):
        has_perm = user.has_perm_to_view
        return u', '.join(unicode(e)
                            for e in entity.get_related_entities(self._rtype.id, True)
                                if has_perm(e)
                         )

    def get_linkable_ctypes(self):
        return self._rtype.object_ctypes.all()

    @property
    def relation_type(self):
        return self._rtype


@REPORT_HANDS_MAP(RFT_FUNCTION)
class RHFunctionField(ReportHand):
    verbose_name = _(u'Computed field')

    def __init__(self, report_field):
        funcfield = report_field.model.function_fields.get(report_field.name)
        if not funcfield:
            raise ReportHand.ValueError('Invalid function field: "%s"' % report_field.name)

        self._funcfield = funcfield

        super(RHFunctionField, self).__init__(report_field, title=unicode(funcfield.verbose_name))

    def _get_value_single_on_allowed(self, entity, user, scope):
        return self._funcfield(entity).for_csv()


class RHAggregate(ReportHand):
    verbose_name = _(u'Aggregated value')

    def __init__(self, report_field):
        self._cache_key   = None
        self._cache_value = None
        field_name, aggregation_id = report_field.name.split('__', 1)
        aggregation = field_aggregation_registry.get(aggregation_id)

        if aggregation is None:
            raise ReportHand.ValueError('Invalid aggregation: "%s"' % aggregation_id)

        self._aggregation_q, verbose_name = self._build_query_n_vname(report_field,
                                                                      field_name,
                                                                      aggregation,
                                                                     )

        super(RHAggregate, self).__init__(report_field,
                                          title=u'%s - %s' % (aggregation.title,
                                                              verbose_name,
                                                             ),
                                         )

    def _build_query_n_vname(self, report_field, field_name, aggregation):
        raise NotImplementedError

    def _get_value_single(self, entity, user, scope):
        if self._cache_key is scope:
            return self._cache_value

        self._cache_key = scope
        self._cache_value = result = scope.aggregate(rh_calculated_agg=self._aggregation_q) \
                                          .get('rh_calculated_agg') or 0

        return result


@REPORT_HANDS_MAP(RFT_AGG_FIELD)
class RHAggregateRegularField(RHAggregate):
    def _build_query_n_vname(self, report_field, field_name, aggregation):
        try:
            field = report_field.model._meta.get_field(field_name)
        except FieldDoesNotExist:
            raise ReportHand.ValueError('Unknown field: "%s"' % field_name)

        if not isinstance(field, field_aggregation_registry.authorized_fields):
            raise ReportHand.ValueError('This type of field can not be aggregated: "%s"' % field_name)

        return (aggregation.func(field_name), field.verbose_name)


@REPORT_HANDS_MAP(RFT_AGG_CUSTOM)
class RHAggregateCustomField(RHAggregate):
    verbose_name = _(u'Aggregated value (custom field)')

    def _build_query_n_vname(self, report_field, field_name, aggregation):
        try:
            cfield = CustomField.objects.get(id=field_name)
        except (ValueError, CustomField.DoesNotExist):
            raise ReportHand.ValueError('Invalid custom field aggregation: "%s"' % field_name)

        if cfield.field_type not in field_aggregation_registry.authorized_customfields:
            raise ReportHand.ValueError('This type of custom field can not be aggregated: "%s"' % field_name)

        return (aggregation.func('%s__value' % cfield.get_value_class().get_related_name()),
                cfield.name,
               )


@REPORT_HANDS_MAP(RFT_RELATED)
class RHRelated(ReportHand):
    verbose_name = _(u'Related field')

    def __init__(self, report_field):
#        related_field = get_related_field(report_field.model, report_field.name)
        related_field = self._get_related_field(report_field.model, report_field.name)

        if not related_field:
            raise ReportHand.ValueError('Invalid related field: "%s"' % report_field.name)

        self._related_field = related_field
        self._attr_name = related_field.get_accessor_name()

        super(RHRelated, self).__init__(report_field,
#                                        title=unicode(related_field.model._meta.verbose_name),
                                        title=unicode(related_field.related_model._meta.verbose_name),
                                        support_subreport=True,
                                       )

    def _get_related_field(self, model, related_field_name):
        for f in model._meta.get_fields():
            if (f.one_to_many or f.one_to_one) and f.name == related_field_name:
                return f

    def _get_related_instances(self, entity, user):
        return getattr(entity, self._attr_name).filter(is_deleted=False)

    def get_linkable_ctypes(self):
#        return (ContentType.objects.get_for_model(self._related_field.model),)
        return (ContentType.objects.get_for_model(self._related_field.related_model),)


class ExpandableLine(object):
    """Store a line of report values that can be expanded in several lines if
    there are selected sub-reports.
    """
    def __init__(self, values):
        self._cvalues = values

    def _visit(self, lines, current_line):
        values = []
        values_to_build = None

        for col_value in self._cvalues:
            if isinstance(col_value, list):
                values.append(None)
                values_to_build = col_value
            else:
                values.append(col_value)

        if None in current_line:
            idx = current_line.index(None)
            current_line[idx:idx + 1] = values
        else:
            current_line.extend(values)

        if values_to_build is not None:
            for future_node in values_to_build:
                ExpandableLine(future_node)._visit(lines, list(current_line))
        else:
            lines.append(current_line)

    def get_lines(self):
        lines = []
        self._visit(lines, [])

        return lines
