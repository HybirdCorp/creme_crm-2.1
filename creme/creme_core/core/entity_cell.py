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

from django.contrib.contenttypes.models import ContentType
from django.db.models import (Field, FieldDoesNotExist, BooleanField, PositiveIntegerField,
        DecimalField, DateField, DateTimeField, ForeignKey, ManyToManyField)
from django.utils.translation import ugettext_lazy as _

from ..models import CremeEntity, RelationType, CustomField
from ..models.fields import DatePeriodField
from ..utils.meta import FieldInfo
from .function_field import FunctionFieldDecimal


logger = logging.getLogger(__name__)


class EntityCellsRegistry(object):
    __slots__ = ('_cell_classes', )

    class RegistrationError(Exception):
        pass

    def __init__(self):
        self._cell_classes = {}

    def __call__(self, cls):
        if self._cell_classes.setdefault(cls.type_id, cls) is not cls:
            raise self.RegistrationError("Duplicated Cell id: %s" % cls.id)

        return cls

    def build_cells_from_dicts(self, model, dicts):
        "@return tuple(list_of_cells, errors) 'errors' is a boolean"
        cells = []
        errors = False

        try:
            for dict_cell in dicts:
                try:
                    cell = self._cell_classes[dict_cell['type']].build(model, dict_cell['value'])

                    if cell is not None:
                        cells.append(cell)
                    else:
                        errors = True
                except Exception as e:
                    logger.warn('EntityCellsRegistry: %s, %s', e.__class__, e)
                    errors = True
        except Exception as e:
            logger.warn('EntityCellsRegistry: %s, %s', e.__class__, e)
            errors = True

        return cells, errors

CELLS_MAP = EntityCellsRegistry()


class EntityCell(object):
    """Represents a value accessor ; it's a kind of super field. It can
    retrieve a value store in entities (of the same type).
    This values can be (see child classes) :
     - regular fields (in the django model way).
     - custom field (see models.CustomField).
     - function fields (see core.FunctionField).
     - other entities linked by a Relation (of a given RelationType)
     - ...
    """
    type_id = None  # Used for register ; overload in child classes (string type)

    _listview_css_class = None
    _header_listview_css_class = None

    def __init__(self, value='', title=u'Title', has_a_filter=False,
                 editable=False, sortable=False,
                 is_hidden=False, filter_string='',
                ):
        self.value = value
        self.title = title
        self.has_a_filter = has_a_filter # TODO: refactor list view templatetags
        self.editable = editable # TODO: still useful ???
        self.sortable = sortable
        self.is_hidden = is_hidden
        self.filter_string = filter_string # TODO: remove from public interface when quick search has been refactored

    def __repr__(self):
        return u"<EntityCell(type=%s, value='%s')>" % (self.type_id, self.value)

    def __unicode__(self):
        return self.title  # Used by CustomBlockConfigItem block (creme_config)

    def _get_field_class(self):
        return Field

    def _get_listview_css_class(self, attr_name):
        from ..gui.field_printers import field_printers_registry

        listview_css_class = getattr(self, attr_name)

        if listview_css_class is None:
            registry_getter = getattr(field_printers_registry, 'get%s_for_field' % attr_name)
            listview_css_class = registry_getter(self._get_field_class())
            setattr(self, attr_name, listview_css_class)

        return listview_css_class

    @property
    def key(self):
        "Return an ID that should be unique in a EntityCell set"
        return '%s-%s' % (self.type_id, self.value)

    @property
    def listview_css_class(self):
        return self._get_listview_css_class('_listview_css_class')

    @property
    def header_listview_css_class(self):
        return self._get_listview_css_class('_header_listview_css_class')

    @staticmethod
    def populate_entities(cells, entities):
        pass

    # TODO: factorise render_* => like FunctionField, result that can be html, csv...
    def render_html(self, entity, user):
        raise NotImplementedError

    def render_csv(self, entity, user):
        raise NotImplementedError

    def to_dict(self):
        return {'type': self.type_id, 'value': self.value}


# @CELLS_MAP TODO
class EntityCellActions(EntityCell):
    type_id = 'actions'

    def __init__(self):
        super(EntityCellActions, self).__init__(value='entity_actions',
                                                title=_(u'Actions'),
                                               )

    # def render_html(self, entity, user): TODO


@CELLS_MAP
class EntityCellRegularField(EntityCell):
    type_id = 'regular_field'

    def __init__(self, model, name, field_info, is_hidden=False):
        "Use build() instead of using this constructor directly."
        self._model = model
        self._field_info = field_info

        field = field_info[0]
        has_a_filter = True
        sortable = True
        pattern = "%s__icontains"

        # if isinstance(field, (ForeignKey, ManyToManyField)):
        #     if len(field_info) == 1:
        #         pattern = "%s"  # todo: factorise
        #     else:
        #         field = field_info[1]  # The sub-field is considered as the main field
        #
        #         if isinstance(field, (ForeignKey, ManyToManyField)):
        #             pattern = '%s'  # todo: '%s__exact' ?
        #
        #     if isinstance(field, ManyToManyField):
        #         sortable = False
        if len(field_info) > 1:
            if field.many_to_many:
                sortable = False

            # TODO: forbids depth > 2  ?
            field = field_info[-1]  # The sub-field is considered as the main field

        # if isinstance(field, (DateField, DateTimeField)):
        if isinstance(field, DateField):
            pattern = "%s__range"  # TODO: quick search overload this, to use gte/lte when it is needed
        elif isinstance(field, BooleanField):
            pattern = "%s__creme-boolean"
        elif isinstance(field, DatePeriodField):
            has_a_filter = False
            sortable = False
        # elif isinstance(field, (ForeignKey, ManyToManyField)) and \
        #      issubclass(field.rel.to, CremeEntity):
        #     pattern = '%s__header_filter_search_field__icontains'
        # TODO: what about one_to_many & one_to_one ?
        elif field.is_relation and field.related_model:
            pattern = '%s__header_filter_search_field__icontains' \
                      if issubclass(field.rel.to, CremeEntity) else '%s'  # TODO '%s__exact' ?
            if field.many_to_many:
                sortable = False

        super(EntityCellRegularField, self).__init__(value=name,
                                                     title=field_info.verbose_name,
                                                     has_a_filter=has_a_filter,
                                                     editable=True,
                                                     sortable=sortable,
                                                     is_hidden=is_hidden,
                                                     filter_string=pattern % name if has_a_filter else '',
                                                    )

    @staticmethod
    def build(model, name, is_hidden=False):
        try:
            field_info = FieldInfo(model, name)
        except FieldDoesNotExist as e:
            logger.warn('EntityCellRegularField(): problem with field "%s" ("%s")', name, e)
            return None

        return EntityCellRegularField(model, name, field_info, is_hidden)

    @property
    def field_info(self):
        return self._field_info

    def _get_field_class(self):
        return self._field_info[-1].__class__

    @staticmethod
    def populate_entities(cells, entities):
        CremeEntity.populate_fk_fields(entities, [cell.field_info[0].name for cell in cells])

    def render_html(self, entity, user):
        from ..gui.field_printers import field_printers_registry

        self.render_html = printer = \
            field_printers_registry.build_field_printer(entity.__class__, self.value, output='html')

        return printer(entity, user)

    def render_csv(self, entity, user):
        from ..gui.field_printers import field_printers_registry

        self.render_csv = printer = \
            field_printers_registry.build_field_printer(entity.__class__, self.value, output='csv')

        return printer(entity, user)


@CELLS_MAP
class EntityCellCustomField(EntityCell):
    type_id = 'custom_field'

    _CF_PATTERNS = {
            CustomField.BOOL:       '%s__value__creme-boolean',
            CustomField.DATETIME:   '%s__value__range',  # TODO: quick search overload this, to use gte/lte when it is needed
            CustomField.ENUM:       '%s__value__exact',
            CustomField.MULTI_ENUM: '%s__value__exact',
        }
    _CF_CSS = {
        CustomField.DATETIME:   DateTimeField,
        CustomField.INT:        PositiveIntegerField,
        CustomField.FLOAT:      DecimalField,
        CustomField.BOOL:       BooleanField,
        CustomField.ENUM:       ForeignKey,
        CustomField.MULTI_ENUM: ManyToManyField,
    }

    def __init__(self, customfield):
        self._customfield = customfield
        pattern = self._CF_PATTERNS.get(customfield.field_type, '%s__value__icontains')

        super(EntityCellCustomField, self).__init__(value=unicode(customfield.id),
                                                    title=customfield.name,
                                                    has_a_filter=True,
                                                    editable=False,  # TODO: make it editable
                                                    sortable=False,  # TODO: make it sortable ?
                                                    is_hidden=False,
                                                    filter_string=pattern % customfield.get_value_class().get_related_name(),
                                                   )

    @staticmethod
    def build(model, customfield_id):
        ct = ContentType.objects.get_for_model(model)

        try:
            cfield = CustomField.objects.get(content_type=ct, id=customfield_id)
        except CustomField.DoesNotExist:
            logger.warn('EntityCellCustomField: custom field "%s" does not exist', customfield_id)
            return None

        return EntityCellCustomField(cfield)
 
    @property
    def custom_field(self):
        return self._customfield

    def _get_field_class(self):
        return self._CF_CSS.get(self._customfield.field_type, Field)

    @staticmethod
    def populate_entities(cells, entities):
        CremeEntity.populate_custom_values(entities, [cell.custom_field for cell in cells]) # NB: not itervalues()

    def render_html(self, entity, user):
        from django.utils.html import escape
        return escape(self.render_csv(entity, user))

    def render_csv(self, entity, user):
        value = entity.get_custom_value(self.custom_field)
        return value if value is not None else ''


@CELLS_MAP
class EntityCellFunctionField(EntityCell):
    type_id = 'function_field'

    _FUNFIELD_CSS = { # TODO: ClassKeyedMap ?
        FunctionFieldDecimal: DecimalField,
    }

    def __init__(self, func_field):
        self._functionfield = func_field

        super(EntityCellFunctionField, self).__init__(value=func_field.name,
                                                      title=unicode(func_field.verbose_name),
                                                      has_a_filter=func_field.has_filter,
                                                      is_hidden=func_field.is_hidden,
                                                     )

    @staticmethod
    def build(model, func_field_name):
        func_field = model.function_fields.get(func_field_name)

        if func_field is None:
            logger.warn('EntityCellFunctionField: function field "%s" does not exist', func_field_name)
            return None

        return EntityCellFunctionField(func_field)

    @property
    def function_field(self):
        return self._functionfield

    def _get_field_class(self):
        return self._FUNFIELD_CSS.get(self._functionfield.result_type, Field)

    @staticmethod
    def populate_entities(cells, entities):
        for cell in cells:
            cell.function_field.populate_entities(entities)

    def render_html(self, entity, user):
        return self.function_field(entity).for_html()

    def render_csv(self, entity, user):
        return self.function_field(entity).for_csv()


@CELLS_MAP
class EntityCellRelation(EntityCell):
    type_id = 'relation'

    def __init__(self, rtype, is_hidden=False):
        self._rtype = rtype
        super(EntityCellRelation, self).__init__(value=unicode(rtype.id),
                                                 title=rtype.predicate,
                                                 has_a_filter=True,
                                                 is_hidden=is_hidden,
                                                )

    @staticmethod
    def build(model, rtype_id, is_hidden=False):
        try:
            rtype = RelationType.objects.get(pk=rtype_id)
        except RelationType.DoesNotExist:
            logger.warn('EntityCellRelation: relation type "%s" does not exist', rtype_id)
            return None

        return EntityCellRelation(rtype, is_hidden=is_hidden)

    @property
    def relation_type(self):
        return self._rtype

    @staticmethod
    def populate_entities(cells, entities):
        CremeEntity.populate_relations(entities, [cell.relation_type.id for cell in cells])

    def render_html(self, entity, user):
        from ..templatetags.creme_widgets import widget_entity_hyperlink

        related_entities = entity.get_related_entities(self.value, True)

        if not related_entities:
            return u''

        if len(related_entities) == 1:
            return widget_entity_hyperlink(related_entities[0], user)

        relations_list = ['<ul>']
        relations_list.extend(u'<li>%s</li>' % widget_entity_hyperlink(e, user)
                                for e in related_entities
                             )
        relations_list.append('</ul>')

        return u''.join(relations_list)

    def render_csv(self, entity, user):
        has_perm = user.has_perm_to_view
        return u'/'.join(unicode(o)
                            for o in entity.get_related_entities(self.value, True)
                                if has_perm(o)
                        )


# @CELLS_MAP TODO ??
class EntityCellVolatile(EntityCell):
    type_id = 'volatile'

    def __init__(self, value, title, render_func, is_hidden=False):
        self._render_func = render_func
        super(EntityCellVolatile, self).__init__(value=value,
                                                 title=title,
                                                 has_a_filter=True,  # TODO: ??
                                                 is_hidden=is_hidden,
                                                )

    def render_html(self, entity, user):
        return self._render_func(entity)
