# -*- coding: utf-8 -*-

################################################################################
#    Creme is a free/open-source Customer Relationship Management software
#    Copyright (C) 2013  Hybird
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

from datetime import timedelta
from json import dumps as json_encode
import logging

from django.db.models import Min, Max, FieldDoesNotExist, Q
from django.utils.translation import ugettext_lazy as _

from creme.creme_core.models import CremeEntity, RelationType, Relation, CustomField, CustomFieldEnumValue
from creme.creme_core.models.header_filter import HFI_RELATION, HFI_FIELD
from creme.creme_core.utils.meta import get_verbose_field_name

from ..constants import *
from ..report_aggregation_registry import field_aggregation_registry


logger = logging.getLogger(__name__)


#TODO: move to creme_core ?
class ListViewURLBuilder(object):
    def __init__(self, model):
        self._fmt = model.get_lv_absolute_url() + '?q_filter='

    def __call__(self, q_filter):
        return self._fmt + json_encode(q_filter)


class ReportGraphHandRegistry(object):
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


HANDS_MAP = ReportGraphHandRegistry()


class ReportGraphYCalculator(object):
    def __call__(self, entities):
        return 0

    @staticmethod
    def build(graph):
        if graph.is_count:
            calculator = RGYCCount()
        else:
            ordinate = graph.ordinate
            ordinate_col, sep, aggregation_name = ordinate.rpartition('__')
            aggregation = field_aggregation_registry.get(aggregation_name) #TODO: manage invalid aggregation ??

            if ordinate_col.isdigit(): #CustomField
                try:
                    calculator = RGYCCustomField(CustomField.objects.get(pk=ordinate_col), aggregation)
                except CustomField.DoesNotExist:
                    logger.warn('ReportGraphHand: CustomField with id="%s" does not exist', ordinate_col)
                    #TODO: error (notify the user that this graph is deprecated)
                    calculator = ReportGraphYCalculator()
            else: #Regular Field
                #TODO: if field does not exit anymore : notify the user that this graph is deprecated.
                calculator = RGYCField(graph.report.ct.model_class(), ordinate, aggregation, ordinate_col)

        return calculator

    @property
    def verbose_name(self):
        return  '??'


class RGYCCount(ReportGraphYCalculator):
    def __call__(self, entities):
        return entities.count()

    @property
    def verbose_name(self):
        return _('Count')


class RGYCAggregation(ReportGraphYCalculator):
    def __init__(self, aggregation, aggregate_value):
        self._aggregation = aggregation
        self._aggregate_value = aggregate_value

    def __call__(self, entities):
        return entities.aggregate(rgyc_value_agg=self._aggregate_value).get('rgyc_value_agg') or 0

    def _name(self):
        raise NotImplementedError

    @property
    def verbose_name(self):
        return u'%s - %s' % (self._name(), self._aggregation.title)


class RGYCField(RGYCAggregation):
    def __init__(self, model, ordinate, aggregation, field_name): #TODO: store field too ??
        super(RGYCField, self).__init__(aggregation, aggregation.func(field_name))
        self._model = model
        self._field_name = field_name

    def _name(self):
        return get_verbose_field_name(self._model, self._field_name)


class RGYCCustomField(RGYCAggregation):
    def __init__(self, cfield, aggregation):
        super(RGYCCustomField, self).__init__(
            aggregation,
            aggregation.func('%s__value' % cfield.get_value_class().get_related_name()),
           )
        self._cfield = cfield

    def _name(self):
        return self._cfield.name


class ReportGraphHand(object):
    "Class that computes abscissa & ordinate values of a ReportGraph"
    verbose_name = 'OVERLOADME'
    hand_id = None #set by ReportGraphHandRegistry decorator

    def __init__(self, graph):
        self._graph = graph
        self._y_calculator = ReportGraphYCalculator.build(graph)

    def _listview_url_builder(self):
        return ListViewURLBuilder(self._graph.report.ct.model_class())

    def _fetch(self, entities, order):
        #TODO: Python3.3 version: yield from ()
        return
        yield

    def fetch(self, entities, order):
        """Returns the X & Y values.
        @param entities Queryset of CremeEntities.
        @param order 'ASC' or 'DESC'.
        @return A tuple (X, Y). X is a list of string labels.
                Y is a list of numerics, or of tuple (numeric, URL).
        """
        x_values = []; x_append = x_values.append
        y_values = []; y_append = y_values.append

        for x, y in self._fetch(entities, order):
            x_append(x)
            y_append(y)

        return x_values, y_values

    def _get_dates_values(self, entities, abscissa, kind, qdict_builder, date_format, order):
        """
        @param kind 'day', 'month' or 'year'
        @param order 'ASC' or 'DESC'
        @param date_format Format compatible with strftime()
        """
        build_url = self._listview_url_builder()
        entities_filter = entities.filter
        y_value_func = self._y_calculator

        for date in entities.dates(abscissa, kind, order):
            qdict = qdict_builder(date)
            yield date.strftime(date_format), [y_value_func(entities_filter(**qdict)), build_url(qdict)]

    @property
    def verbose_abscissa(self):
        graph = self._graph
        return get_verbose_field_name(graph.report.ct.model_class(), graph.abscissa)

    @property
    def verbose_ordinate(self):
        return self._y_calculator.verbose_name


@HANDS_MAP(RGT_DAY)
class RGHDay(ReportGraphHand):
    verbose_name = _(u"By days")

    def _fetch(self, entities, order):
        abscissa = self._graph.abscissa
        year_key  = '%s__year' % abscissa
        month_key = '%s__month' % abscissa
        day_key   ='%s__day' % abscissa

        return self._get_dates_values(entities, abscissa, 'day',
                                      qdict_builder=lambda date: {year_key:  date.year,
                                                                  month_key: date.month,
                                                                  day_key:   date.day,
                                                                 },
                                      date_format="%d/%m/%Y", order=order,
                                     )

@HANDS_MAP(RGT_MONTH)
class RGHMonth(ReportGraphHand):
    verbose_name = _(u"By months")

    def _fetch(self, entities, order):
        abscissa = self._graph.abscissa
        year_key  = '%s__year' % abscissa
        month_key = '%s__month' % abscissa

        return self._get_dates_values(entities, abscissa, 'month',
                                      qdict_builder=lambda date: {year_key:  date.year,
                                                                  month_key: date.month,
                                                                 },
                                      date_format="%m/%Y", order=order,
                                     )


@HANDS_MAP(RGT_YEAR)
class RGHYear(ReportGraphHand):
    verbose_name =_(u"By years")

    def _fetch(self, entities, order):
        abscissa = self._graph.abscissa

        return self._get_dates_values(entities, abscissa, 'year',
                                      qdict_builder=lambda date: {'%s__year' % abscissa: date.year},
                                      date_format="%Y", order=order,
                                     )

#TODO: move to creme_core ??
class DateInterval(object):
    def __init__(self, begin, end, before=None, after=None):
        self.begin = begin
        self.end = end
        self.before = before or begin
        self.after = after or end

    @staticmethod
    def generate(days_duration, min_date, max_date, order):
        days = timedelta(days_duration)

        if order == 'ASC':
            while min_date <= max_date:
                begin = min_date
                end   = min_date + days
                yield DateInterval(begin, end)

                min_date = end + timedelta(days=1)
        else:
            while min_date <= max_date:
                begin = max_date
                end   = max_date - days
                yield DateInterval(begin, end, end, begin)

                max_date = end - timedelta(days=1)


@HANDS_MAP(RGT_RANGE)
class RGHRange(ReportGraphHand):
    verbose_name = _(u"By X days")

    def _fetch(self, entities, order):
        graph = self._graph
        abscissa = graph.abscissa

        date_aggregates = entities.aggregate(min_date=Min(abscissa), max_date=Max(abscissa))
        min_date = date_aggregates['min_date']
        max_date = date_aggregates['max_date']

        if min_date is not None and max_date is not None:
            build_url = self._listview_url_builder()
            query_cmd = '%s__range' % abscissa
            entities_filter = entities.filter
            y_value_func = self._y_calculator

            for interval in DateInterval.generate((graph.days or 1) - 1, min_date, max_date, order):
                before = interval.before
                after  = interval.after
                sub_entities = entities_filter(**{query_cmd: (before, after)})

                yield ('%s-%s' % (interval.begin.strftime("%d/%m/%Y"), #TODO: use format from settings ??
                                  interval.end.strftime("%d/%m/%Y"),
                                 ),
                       [y_value_func(sub_entities),
                        build_url({query_cmd: [before.strftime("%Y-%m-%d"),
                                               after.strftime("%Y-%m-%d"),
                                              ]
                                  }
                               )
                       ],
                      )


@HANDS_MAP(RGT_FK)
class RGHForeignKey(ReportGraphHand):
    verbose_name = _(u"By values")

    def _fetch(self, entities, order):
        abscissa = self._graph.abscissa
        build_url = self._listview_url_builder()
        entities_filter = entities.filter
        y_value_func = self._y_calculator

        related_instances = list(entities.model._meta.get_field(abscissa).rel.to.objects.all())
        if order == 'DESC':
            related_instances.reverse()

        for instance in related_instances:
            kwargs = {abscissa: instance.id}
            yield unicode(instance), [y_value_func(entities_filter(**kwargs)), build_url(kwargs)]


@HANDS_MAP(RGT_RELATION)
class RGHRelation(ReportGraphHand):
    verbose_name = _(u"By values (of related entities)")

    def __init__(self, graph):
        super(RGHRelation, self).__init__(graph)

        try:
            rtype = RelationType.objects.get(pk=self._graph.abscissa)
        except RelationType.DoesNotExist:
            rtype = None
            #TODO: self.error

        self._rtype = rtype

    def _fetch(self, entities, order):
        rtype = self._rtype

        #TODO: Optimize ! (populate real entities)
        #TODO: make listview url for this case
        if rtype:
            relations = Relation.objects.filter(type=rtype, subject_entity__entity_type=self._graph.report.ct)
            rel_filter = relations.filter
            ce_objects_get = CremeEntity.objects.get
            entities_filter = entities.filter
            y_value_func = self._y_calculator

            for obj_id in relations.values_list('object_entity', flat=True).distinct():
                subj_ids = rel_filter(object_entity=obj_id).values_list('subject_entity')

                yield (unicode(ce_objects_get(pk=obj_id).get_real_entity()),
                       y_value_func(entities_filter(pk__in=subj_ids)),
                      )

    @property
    def verbose_abscissa(self):
        rtype = self._rtype
        return rtype.predicate if rtype else ''


class _RGHCustom(ReportGraphHand):
    def __init__(self, graph):
        super(_RGHCustom, self).__init__(graph)
        abscissa = self._graph.abscissa

        try:
            cfield = CustomField.objects.get(pk=abscissa)
        except CustomField.DoesNotExist:
            logger.warn('ReportGraph.fetch: CustomField with id="%s" does not exist', abscissa)
            cfield = None
            #TODO: self.error (notify the user that this graph is deprecated)

        self._cfield = cfield

    def _get_custom_dates_values(self, entities, abscissa, kind, qdict_builder, date_format, order):
        """
        @param kind 'day', 'month' or 'year'
        @param order 'ASC' or 'DESC'
        @param date_format Format compatible with strftime()
        """
        cfield = self._cfield

        if cfield:
            build_url = self._listview_url_builder()
            entities_filter = entities.filter
            y_value_func = self._y_calculator

            for date in entities_filter(customfielddatetime__custom_field=cfield) \
                                       .dates('customfielddatetime__value', kind, order):
                qdict = qdict_builder(date)
                qdict['customfielddatetime__custom_field'] = cfield.id

                yield date.strftime(date_format), [y_value_func(entities_filter(**qdict)), build_url(qdict)]

    @property
    def verbose_abscissa(self):
        cfield = self._cfield
        return cfield.name if cfield else ''


@HANDS_MAP(RGT_CUSTOM_DAY)
class RGHCustomDay(_RGHCustom):
    verbose_name = _(u"By days")

    def _fetch(self, entities, order):
        return self._get_custom_dates_values(entities, self._graph.abscissa, 'day',
                                             qdict_builder=lambda date: {'customfielddatetime__value__year':  date.year,
                                                                         'customfielddatetime__value__month': date.month,
                                                                         'customfielddatetime__value__day':   date.day,
                                                                        },
                                             date_format="%d/%m/%Y", order=order,
                                            )


@HANDS_MAP(RGT_CUSTOM_MONTH)
class RGHCustomMonth(_RGHCustom):
    verbose_name = _(u"By months")

    def _fetch(self, entities, order):
        return self._get_custom_dates_values(entities, self._graph.abscissa, 'month',
                                             qdict_builder=lambda date: {'customfielddatetime__value__year':  date.year,
                                                                         'customfielddatetime__value__month': date.month,
                                                                        },
                                             date_format="%m/%Y", order=order,
                                            )


@HANDS_MAP(RGT_CUSTOM_YEAR)
class RGHCustomYear(_RGHCustom):
    verbose_name = _(u"By years")

    def _fetch(self, entities, order):
        return self._get_custom_dates_values(entities, self._graph.abscissa, 'year',
                                             qdict_builder=lambda date: {'customfielddatetime__value__year': date.year},
                                             date_format="%Y", order=order,
                                            )


@HANDS_MAP(RGT_CUSTOM_RANGE)
class RGHCustomRange(_RGHCustom):
    verbose_name = _(u"By X days")

    def _fetch(self, entities, order):
        cfield = self._cfield

        if cfield:
            date_aggregates = entities.aggregate(min_date=Min('customfielddatetime__value'),
                                                 max_date=Max('customfielddatetime__value'),
                                                ) #TODO: several cf...
            min_date = date_aggregates['min_date']
            max_date = date_aggregates['max_date']

            if min_date is not None and max_date is not None:
                entities_filter = entities.filter
                y_value_func = self._y_calculator
                build_url = self._listview_url_builder()

                for interval in DateInterval.generate((self._graph.days or 1) - 1, min_date, max_date, order):
                    before = interval.before
                    after  = interval.after
                    sub_entities = entities_filter(customfielddatetime__value__range=(before, after))

                    yield ('%s-%s' % (interval.begin.strftime("%d/%m/%Y"), #TODO: use format from settings ??
                                      interval.end.strftime("%d/%m/%Y"),
                                     ),
                           [y_value_func(sub_entities),
                            build_url({'customfielddatetime__value__range': [before.strftime("%Y-%m-%d"),
                                                                             after.strftime("%Y-%m-%d"),
                                                                            ],
                                      }
                                     )
                           ]
                          )


@HANDS_MAP(RGT_CUSTOM_FK)
class RGHCustomFK(_RGHCustom):
    verbose_name = _(u"By values (of custom choices)")

    def _fetch(self, entities, order):
        cfield = self._cfield

        if cfield:
            entities_filter = entities.filter
            y_value_func = self._y_calculator
            build_url = self._listview_url_builder()
            related_instances = list(CustomFieldEnumValue.objects.filter(custom_field=cfield))

            if order == 'DESC':
                related_instances.reverse()

            for instance in related_instances:
                kwargs = {'customfieldenum__value': instance.id}

                yield unicode(instance), [y_value_func(entities_filter(**kwargs)), build_url(kwargs)]


def fetch_graph_from_instance_block(instance_block, entity, order='ASC'):
    volatile_column = instance_block.data
    graph           = instance_block.entity.get_real_entity()
    ct_entity       = entity.entity_type #entity should always be a CremeEntity because graphs can be created only on CremeEntities

    columns = volatile_column.split('|')
    volatile_column, hfi_type = (columns[0], columns[1]) if columns[0] else ('', 0)

    try:
        hfi_type = int(hfi_type)
    except ValueError:
        hfi_type = 0

    x = []
    y = []

    if hfi_type == HFI_FIELD: #TODO: unit test
        try:
            field = graph.report.ct.model_class()._meta.get_field(volatile_column)
        except FieldDoesNotExist:
            pass
        else:
            if field.get_internal_type() == 'ForeignKey' and field.rel.to == entity.__class__: #TODO: use isinstance()
                x, y = graph.fetch(extra_q=Q(**{str('%s__pk' % volatile_column): entity.pk}), #TODO: str() ??
                                   order=order
                                  )
    elif hfi_type == HFI_RELATION: #TODO: unit test
        try:
            rtype = RelationType.objects.get(pk=volatile_column)
        except RelationType.DoesNotExist:
            pass
        else:
            obj_ctypes = rtype.object_ctypes.all()

            if not obj_ctypes or ct_entity in obj_ctypes: #TODO: use RelationType.is_compatible
                x, y = graph.fetch(extra_q=Q(relations__type=rtype,
                                             relations__object_entity=entity.pk,
                                            ),
                                   order=order
                                  )
    else:
        x, y = graph.fetch(order=order)

    return (x, y)
