# -*- coding: utf-8 -*-

################################################################################
#    Creme is a free/open-source Customer Relationship Management software
#    Copyright (C) 2009-2015  Hybird
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

from future_builtins import map
from collections import defaultdict
from copy import deepcopy
from itertools import chain
from json import loads as json_load, dumps as json_dump
from re import compile as compile_re
import warnings

from django.core.validators import validate_email
from django.contrib.contenttypes.models import ContentType
from django.db.models.query import QuerySet
from django.forms import (Field, CharField, MultipleChoiceField, ChoiceField,
        ModelChoiceField, DateField, TimeField, DateTimeField, IntegerField)
from django.forms.utils import ValidationError
from django.forms.widgets import Select, Textarea
from django.forms.fields import EMPTY_VALUES, MultiValueField, RegexField
from django.utils.encoding import smart_unicode
from django.utils.translation import ugettext_lazy as _

from ..constants import REL_SUB_HAS
from ..models import RelationType, CremeEntity, EntityFilter
from ..utils import creme_entity_content_types, build_ct_choices, find_first
from ..utils.collections import OrderedSet
from ..utils.date_period import date_period_registry
from ..utils.date_range import date_range_registry
from ..utils.queries import get_q_from_dict
from .widgets import (CTEntitySelector, EntitySelector, FilteredEntityTypeWidget,
        SelectorList, RelationSelector, ActionButtonList,
        ListEditionWidget, UnorderedMultipleChoiceWidget,
        CalendarWidget, TimeWidget, DatePeriodWidget, DateRangeWidget,
        ColorPickerWidget, DurationWidget, ChoiceOrCharWidget) #ListViewWidget


__all__ = ('GenericEntityField', 'MultiGenericEntityField',
           'RelationEntityField', 'MultiRelationEntityField',
           'CreatorEntityField', 'MultiCreatorEntityField',
           #'CremeEntityField', 'MultiCremeEntityField',
           'FilteredEntityTypeField',
           'ListEditionField',
           'AjaxChoiceField', 'AjaxMultipleChoiceField', 'AjaxModelChoiceField',
           'CremeTimeField', 'CremeDateField', 'CremeDateTimeField',
           'DatePeriodField', 'DateRangeField', 'ColorField', 'DurationField',
           'CTypeChoiceField', 'EntityCTypeChoiceField',
           'MultiCTypeChoiceField', 'MultiEntityCTypeChoiceField',
          )


class JSONField(CharField):
    default_error_messages = {
        'invalidformat': _(u'Invalid format'),
        'invalidtype': _(u'Invalid type'),
        'doesnotexist': _(u"This entity doesn't exist."),
    }
    value_type = None #Overload this: type of the value returned by the field.

    def _build_empty_value(self):
        "Value returned by not-required fields, when value is empty."
        if self.value_type is list:
            return []

        return None

    def _return_none_or_raise(self, required, error_key='required'):
        if required:
            raise ValidationError(self.error_messages[error_key])

        return None

    def _return_list_or_raise(self, required, error_key='required'):
        if required:
            raise ValidationError(self.error_messages[error_key])

        return []

    def clean_value(self, data, name, type, required=True, required_error_key='required'):
        if not data:
            raise ValidationError(self.error_messages['invalidformat'],
                                  code='invalidformat',
                                 )

        if not isinstance(data, dict):
            raise ValidationError(self.error_messages['invalidformat'],
                                  code='invalidformat',
                                 )

        value = data.get(name)

        #value can be "False" if a boolean value is expected.
        if value is None:
            return self._return_none_or_raise(required, required_error_key)

        if isinstance(value, type):
            return value

        if value == '' and not required:
            return None

        try:
            return type(value)
        except:
            raise ValidationError(self.error_messages['invalidformat'],
                                  code='invalidformat',
                                 )

    def clean_json(self, value, expected_type=None):
        if not value:
            return self._return_none_or_raise(self.required)

        try:
            data = json_load(value)
        except Exception:
            raise ValidationError(self.error_messages['invalidformat'],
                                  code='invalidformat',
                                 )

        if expected_type is not None and data is not None and not isinstance(data, expected_type):
            raise ValidationError(self.error_messages['invalidtype'], code='invalidtype')

        return data

    def format_json(self, value):
        return json_dump(value)

    #TODO: can we remove this hack with the new widget api (since django 1.2) ??
    def from_python(self, value):
        if not value:
            return ''

        if isinstance(value, basestring):
            return value

        return self.format_json(self._value_to_jsonifiable(value))

    def clean(self, value):
        data = self.clean_json(value, expected_type=self.value_type)

        if not data:
            if self.required:
                raise ValidationError(self.error_messages['required'], code='required')

            return self._build_empty_value()

        return self._value_from_unjsonfied(data)

    def _clean_entity(self, ctype, entity_pk):
        "@param ctype ContentType instance or PK."
        if not isinstance(ctype, ContentType):
            try:
                ctype = ContentType.objects.get_for_id(ctype)
            except ContentType.DoesNotExist:
                raise ValidationError(self.error_messages['doesnotexist'],
                                      params={'ctype': ctype},
                                      code='doesnotexist',
                                     )

        entity = None

        if not entity_pk:
            if self.required:
                raise ValidationError(self.error_messages['required'], code='required')
        else:
            model = ctype.model_class()
            assert issubclass(model, CremeEntity)

            try:
                entity = model.objects.get(is_deleted=False, pk=entity_pk)
            except model.DoesNotExist:
                raise ValidationError(self.error_messages['doesnotexist'],
                                      params={'ctype': ctype.pk,
                                              'entity': entity_pk,
                                             },
                                      code='doesnotexist',
                                     )

        return entity

    def _entity_queryset(self, model, qfilter=None):
        query = model.objects.filter(is_deleted=False)

        if qfilter is not None:
            query = query.filter(qfilter)

        return query

    def _clean_entity_from_model(self, model, entity_pk, qfilter=None):
        try:
            return self._entity_queryset(model, qfilter).get(pk=entity_pk)
        except model.DoesNotExist:
            if self.required:
                raise ValidationError(self.error_messages['doesnotexist'],
                                      code='doesnotexist',
                                     )

    def _create_widget(self):
        #pass
        raise NotImplementedError

    def _build_widget(self):
        self.widget = self._create_widget()
        #TODO : wait for django 1.2 and new widget api to remove this hack
        self.widget.from_python = lambda v: self.from_python(v)

    def _value_from_unjsonfied(self, data):
        "Build the field value from deserialized data."
        return data

    def _value_to_jsonifiable(self, value):
        "Convert the python value to jsonifiable object."
        return value


class GenericEntityField(JSONField):
    default_error_messages = {
        'ctypenotallowed': _(u"This content type is not allowed."),
        'ctyperequired':   _(u"The content type is required."),
        'doesnotexist':    _(u"This entity doesn't exist."),
        'entityrequired':  _(u"The entity is required."),
    }
    value_type = dict

    def __init__(self, models=None, autocomplete=False, *args, **kwargs):
        super(GenericEntityField, self).__init__(*args, **kwargs)
        self._autocomplete = autocomplete
        self.allowed_models = models

    @property
    def allowed_models(self):
        return self._allowed_models

    @allowed_models.setter
    def allowed_models(self, allowed=()):
        self._allowed_models = allowed if allowed else list()
        self._build_widget()

    @property
    def autocomplete(self):
        return self._autocomplete

    @autocomplete.setter
    def autocomplete(self, autocomplete):
        self._autocomplete = autocomplete
        self._build_widget()

    def _create_widget(self):
        return CTEntitySelector(self._get_ctypes_options(self.get_ctypes()),
                                attrs={'reset': not self.required},
                               )

    def _value_to_jsonifiable(self, value):
        if isinstance(value, CremeEntity):
            ctype = value.entity_type_id
            pk = value.id
        else:
            #ctype = value['ctype']
            #pk = value['entity']
            return value

        return {'ctype': ctype, 'entity': pk}

    def _value_from_unjsonfied(self, data):
        clean_value = self.clean_value
        required = self.required

        ctype_pk  = clean_value(data, 'ctype',  int, required, 'ctyperequired')
        entity_pk = clean_value(data, 'entity', int, required, 'entityrequired')

        return self._clean_entity(self._clean_ctype(ctype_pk), entity_pk)

    def _clean_ctype(self, ctype_pk):
        #check ctype in allowed ones
        for ct in self.get_ctypes():
            if ct.pk == ctype_pk:
                return ct

        raise ValidationError(self.error_messages['ctypenotallowed'], code='ctypenotallowed')

    def _get_ctypes_options(self, ctypes):
        return ((ctype.pk, unicode(ctype)) for ctype in ctypes)

    def get_ctypes(self):
        get_ct = ContentType.objects.get_for_model
        return [get_ct(model) for model in self._allowed_models] if self._allowed_models \
               else list(creme_entity_content_types())


#TODO: Add a q_filter, see utilization in EntityEmailForm
#TODO: propose to allow duplicates ???
class MultiGenericEntityField(GenericEntityField):
    value_type = list

    def __init__(self, models=None, autocomplete=False, unique=True, *args, **kwargs):
        super(MultiGenericEntityField, self).__init__(models, autocomplete, *args, **kwargs)
        self.unique = unique

    def _create_widget(self):
        return SelectorList(CTEntitySelector(self._get_ctypes_options(self.get_ctypes()), multiple=True))

    def _value_to_jsonifiable(self, value):
        return list(map(super(MultiGenericEntityField, self)._value_to_jsonifiable, value))

    def _value_from_unjsonfied(self, data):
        entities_pks = OrderedSet() if self.unique else []#in order to keep the global order (left by defaultdict)
        entities_pks_append = entities_pks.add if self.unique else entities_pks.append

        entities_by_ctype = defaultdict(list)
        clean_value = self.clean_value

        #group entity PKs by ctype, in order to make efficient queries
        for entry in data:
            ctype_pk = clean_value(entry, 'ctype', int, required=False)
            if not ctype_pk:
                continue

            entity_pk = clean_value(entry, 'entity', int, required=False)
            if not entity_pk:
                continue

            entities_pks_append(entity_pk)
            entities_by_ctype[ctype_pk].append(entity_pk)

        entities = {}

        #build the list of entities (ignore invalid entries)
        for ct_id, ctype_entity_pks in entities_by_ctype.iteritems():
            ctype_entities = self._clean_ctype(ct_id).model_class() \
                                                     .objects \
                                                     .filter(is_deleted=False) \
                                                     .in_bulk(ctype_entity_pks)

            if not all(pk in ctype_entities for pk in ctype_entity_pks):
                raise ValidationError(self.error_messages['doesnotexist'],
                                      code='doesnotexist',
                                     )

            entities.update(ctype_entities)

        if not entities:
            return self._return_list_or_raise(self.required)

        return [entities[pk] for pk in entities_pks]


class ChoiceModelIterator(object):
    def __init__(self, queryset, render_value=None, render_label=None):
        self.queryset = queryset.all()
        self.render_value = render_value or (lambda v: v.pk)
        self.render_label = render_label or (lambda v: unicode(v))

    def __iter__(self):
        for model in self.queryset:
            yield (self.render_value(model), self.render_label(model))

    def __len__(self):
        return len(self.queryset)


class RelationEntityField(JSONField):
    default_error_messages = {
        'rtypedoesnotexist': _(u"This type of relationship doesn't exist."),
        'rtypenotallowed':   _(u"This type of relationship causes a constraint error."),
        'ctyperequired':     _(u"The content type is required."),
        'ctypenotallowed':   _(u"This content type cause constraint error with the type of relationship."),
        'entityrequired':    _(u"The entity is required."),
        'doesnotexist':      _(u"This entity doesn't exist."),
        'nopropertymatch':   _(u"This entity has no property that matches the constraints of the type of relationship."),
    }
    value_type = dict

    @property
    def allowed_rtypes(self):
        return self._allowed_rtypes

    @allowed_rtypes.setter
    def allowed_rtypes(self, allowed=(REL_SUB_HAS, )):
        if allowed:
            rtypes = allowed if isinstance(allowed, QuerySet) else RelationType.objects.filter(id__in=allowed)
            rtypes = rtypes.order_by('predicate') #TODO: meta.ordering ??
        else:
            rtypes = RelationType.objects.order_by('predicate')

        self._allowed_rtypes = rtypes
        self._build_widget()

    @property
    def autocomplete(self):
        return self._autocomplete

    @autocomplete.setter
    def autocomplete(self, autocomplete):
        self._autocomplete = autocomplete
        self._build_widget()

    def __init__(self, allowed_rtypes=(REL_SUB_HAS, ), autocomplete=False, *args, **kwargs):
        super(RelationEntityField, self).__init__(*args, **kwargs)
        self._autocomplete = autocomplete
        self.allowed_rtypes = allowed_rtypes

    def _create_widget(self):
        return RelationSelector(self._get_options,
                                '/creme_core/relation/type/${rtype}/content_types/json',
                                autocomplete=self.autocomplete,
                                attrs={'reset': not self.required},
                               )

    def _value_to_jsonifiable(self, value):
        rtype, entity = value

        return {'rtype': rtype.pk, 'ctype': entity.entity_type_id, 'entity': entity.pk} if entity else \
               {'rtype': rtype.pk, 'ctype': None,                  'entity': None}

    def _value_from_unjsonfied(self, data):
        clean_value = self.clean_value
        rtype_pk = clean_value(data, 'rtype',  str)

        ctype_pk  = clean_value(data, 'ctype',  int, required=False)
        if not ctype_pk:
            return self._return_none_or_raise(self.required, 'ctyperequired')

        entity_pk = clean_value(data, 'entity', int, required=False)
        if not entity_pk:
            return self._return_none_or_raise(self.required, 'entityrequired')

        rtype = self._clean_rtype(rtype_pk)
        self._validate_ctype_constraints(rtype, ctype_pk)

        entity = self._clean_entity(ctype_pk, entity_pk)
        self._validate_properties_constraints(rtype, entity)

        return (rtype, entity)

    def _validate_ctype_constraints(self, rtype, ctype_pk):
        ctype_ids = rtype.object_ctypes.values_list('pk', flat=True)

        # is relation type accepts content type
        if ctype_ids and ctype_pk not in ctype_ids:
            raise ValidationError(self.error_messages['ctypenotallowed'],
                                  params={'ctype': ctype_pk}, code='ctypenotallowed',
                                 )

    def _validate_properties_constraints(self, rtype, entity):
        ptype_ids = frozenset(rtype.object_properties.values_list('id', flat=True))

        if ptype_ids and not any(p.type_id in ptype_ids for p in entity.get_properties()):
            raise ValidationError(self.error_messages['nopropertymatch'],
                                  code='nopropertymatch',
                                 )

    def _clean_rtype(self, rtype_pk):
        # is relation type allowed
        if rtype_pk not in self._get_allowed_rtypes_ids():
            raise ValidationError(self.error_messages['rtypenotallowed'],
                                  params={'rtype': rtype_pk}, code='rtypenotallowed',
                                 )

        try:
            return RelationType.objects.get(pk=rtype_pk)
        except RelationType.DoesNotExist:
            raise ValidationError(self.error_messages['rtypedoesnotexist'],
                                  params={'rtype': rtype_pk}, code='rtypedoesnotexist',
                                 )

    def _get_options(self):
        return ChoiceModelIterator(self._allowed_rtypes)

    def _get_allowed_rtypes_objects(self):
        return self._allowed_rtypes.all()

    def _get_allowed_rtypes_ids(self):
        return self._allowed_rtypes.values_list('id', flat=True)


class MultiRelationEntityField(RelationEntityField):
    value_type = list

    def _create_widget(self):
        return SelectorList(RelationSelector(self._get_options,
                                             '/creme_core/relation/type/${rtype}/content_types/json',
                                             multiple=True,
                                             autocomplete=self.autocomplete
                                            )
                           )

    def _value_to_jsonifiable(self, value):
        return list(map(super(MultiRelationEntityField, self)._value_to_jsonifiable, value))

    def _build_rtype_cache(self, rtype_pk):
        try:
            rtype = RelationType.objects.get(pk=rtype_pk)
        except RelationType.DoesNotExist:
            raise ValidationError(self.error_messages['rtypedoesnotexist'],
                                  params={'rtype': rtype_pk}, code='rtypedoesnotexist',
                                 )

        rtype_allowed_ctypes     = frozenset(ct.pk for ct in rtype.object_ctypes.all())
        rtype_allowed_properties = frozenset(rtype.object_properties.values_list('id', flat=True))

        return (rtype, rtype_allowed_ctypes, rtype_allowed_properties)

    def _build_ctype_cache(self, ctype_pk):
        try:
            ctype = ContentType.objects.get_for_id(ctype_pk)
        except ContentType.DoesNotExist:
            raise ValidationError(self.error_messages['ctypedoesnotexist'],
                                  params={'ctype': ctype_pk}, code='ctypedoesnotexist',
                                 )

        return (ctype, [])

    def _get_cache(self, entries, key, build_func):
        cache = entries.get(key)

        if not cache:
            cache = build_func(key)
            entries[key] = cache

        return cache

    def _value_from_unjsonfied(self, data):
        clean_value = self.clean_value
        cleaned_entries = []

        for entry in data:
            rtype_pk = clean_value(entry, 'rtype', str)

            ctype_pk =  clean_value(entry, 'ctype', int, required=False)
            if not ctype_pk:
                continue

            entity_pk = clean_value(entry, 'entity', int, required=False)
            if not entity_pk:
                continue

            cleaned_entries.append((rtype_pk, ctype_pk, entity_pk))

        rtypes_cache = {}
        ctypes_cache = {}
        allowed_rtypes_ids = frozenset(self._get_allowed_rtypes_ids())

        need_property_validation = False

        for rtype_pk, ctype_pk, entity_pk in cleaned_entries:
            # check if relation type is allowed
            if rtype_pk not in allowed_rtypes_ids:
                raise ValidationError(self.error_messages['rtypenotallowed'],
                                      params={'rtype': rtype_pk,
                                              'ctype': ctype_pk,
                                             },
                                      code='rtypenotallowed',
                                     )

            rtype, rtype_allowed_ctypes, rtype_allowed_properties = \
                self._get_cache(rtypes_cache, rtype_pk, self._build_rtype_cache)

            if rtype_allowed_properties:
                need_property_validation = True

            # check if content type is allowed by relation type
            if rtype_allowed_ctypes and ctype_pk not in rtype_allowed_ctypes:
                raise ValidationError(self.error_messages['ctypenotallowed'],
                                      params={'ctype':ctype_pk}, code='ctypenotallowed',
                                     )

            ctype, ctype_entity_pks = self._get_cache(ctypes_cache, ctype_pk,
                                                      self._build_ctype_cache,
                                                     )
            ctype_entity_pks.append(entity_pk)

        entities_cache = {}

        #build real entity cache and check both entity id exists and in correct content type
        for ctype, entity_pks in ctypes_cache.values():
            ctype_entities = {entity.pk: entity
                                for entity in ctype.model_class()
                                                   .objects
                                                   .filter(is_deleted=False, pk__in=entity_pks)
                             }

            if not all(entity_pk in ctype_entities for entity_pk in entity_pks):
                raise ValidationError(self.error_messages['doesnotexist'],
                                      code='doesnotexist',
                                     )

            entities_cache.update(ctype_entities)

        relations = []

        # build cache for validation of properties constraint between relationtypes and entities
        if need_property_validation:
            CremeEntity.populate_properties(entities_cache.values())

        for rtype_pk, ctype_pk, entity_pk in cleaned_entries:
            rtype, rtype_allowed_ctypes, rtype_allowed_properties = rtypes_cache.get(rtype_pk)
            entity = entities_cache.get(entity_pk)

            if rtype_allowed_properties and \
               not any(p.type_id in rtype_allowed_properties for p in entity.get_properties()):
                raise ValidationError(self.error_messages['nopropertymatch'],
                                      code='nopropertymatch',
                                     )

            relations.append((rtype, entity))

        if not relations:
            return self._return_list_or_raise(self.required)

        return relations


class CreatorEntityField(JSONField):
    default_error_messages = {
        'doesnotexist':    _(u"This entity doesn't exist."),
        'entityrequired':  _(u"The entity is required."),
    }
    value_type = int

    def __init__(self, model=None, q_filter=None, create_action_url=None, *args, **kwargs):
        super(CreatorEntityField, self).__init__(*args, **kwargs)
        self._model = model
        self._user = None
        self._create_action_url = create_action_url
        self.q_filter = q_filter

    @property
    def model(self):
        return self._model

    @model.setter
    def model(self, model=None):
        self._model = model
        self._build_widget()
        self._update_actions()

    @property
    def q_filter(self):
        return self._q_filter

    @q_filter.setter
    def q_filter(self, q_filter):
        self._q_filter = q_filter

        if self.model is not None:
            self._build_widget()
            self._update_actions()

    @property
    def q_filter_query(self):
        try:
            q_filter = self._q_filter
            return get_q_from_dict(q_filter) if q_filter is not None else None
        except:
            raise ValueError('Invalid q_filter %s' % q_filter)

    @property
    def create_action_url(self):
        if self._create_action_url is not None:
            return self._create_action_url

        return '/creme_core/quickforms/from_widget/%s/add/1' % self.get_ctype().pk

    @create_action_url.setter
    def create_action_url(self, url):
        self._create_action_url = url

        if self.widget is not None:
            self._update_actions()

    @property
    def user(self):
        return self._user

    @user.setter
    def user(self, user):
        self._user = user
        self._update_actions()

    def _update_actions(self):
        user = self._user
        self._clear_actions()

        if not self.required:
            self._add_action('reset', _(u'Clear'), title=_(u'Clear'), action='reset', value='')

        if self._q_filter is not None and self._create_action_url is None:
            return

        if user is not None:
            self._add_create_action(user)

    def _clear_actions(self):
        self.widget.clear_actions()

    def _add_action(self, name, label, **kwargs):
        self.widget.add_action(name, label, **kwargs)

    def _has_quickform(self, model):
        from creme.creme_core.gui import quickforms_registry
        return quickforms_registry.get_form(model) is not None

    def _add_create_action(self, user):
        model = self.model

        if not self._has_quickform(model):
            return

        allowed = user.has_perm_to_create(model)
        self._add_action('create', _(u'Add'), enabled=allowed,
                         title=_(u'Add') if allowed else _(u"Can't add"),
                         url=self.create_action_url,
                        )

    def _create_widget(self):
        return ActionButtonList(delegate=EntitySelector(unicode(self.get_ctype().pk),
                                                        {'auto':    False,
                                                         'qfilter': self.q_filter,
                                                        },
                                                       )
                               )

    def _value_to_jsonifiable(self, value):
        if isinstance(value, (int, long)):
            if not self._entity_queryset(self.model, self.q_filter_query).filter(pk=value).exists():
                raise ValueError('No such entity with id %d.' % value)

            return value

        assert isinstance(value, CremeEntity)
        return value.id

    def _value_from_unjsonfied(self, data):
        return self._clean_entity_from_model(self.model, data, self.q_filter_query)

    def get_ctype(self):
        model = self.model
        return ContentType.objects.get_for_model(model) if model is not None else None


class MultiCreatorEntityField(CreatorEntityField):
    value_type = list

    def _create_widget(self):
        self._widget_item = ActionButtonList(delegate=EntitySelector(unicode(self.get_ctype().pk),
                                                                     {'auto':       False,
                                                                      'qfilter':    self.q_filter,
                                                                      'multiple':   True,
                                                                      'autoselect': True,
                                                                     },
                                                                    )
                                            )

        return SelectorList(self._widget_item,
                            attrs={'clonelast' : False},
                           )

    def _clear_actions(self):
        self._widget_item.clear_actions()
        self.widget.clear_actions()

    def _add_action(self, name, label, is_list_action=False, **kwargs):
        enabled = kwargs.pop('enabled', True)

        if is_list_action:
            self._widget_item.add_action(name, label, enabled=False, **kwargs)
            self.widget.add_action(name, label, enabled)
        else:
            self._widget_item.add_action(name, label, enabled=enabled, **kwargs)

    def _add_create_action(self, user):
        model = self.model

        if not self._has_quickform(model):
            return

        allowed = user.has_perm_to_create(model)

        self._add_action('create', model.creation_label, enabled=allowed,
                         title=_(u'Create') if allowed else _(u"Can't create"),
                         url=self.create_action_url,
                         is_list_action=True,
                        )

    def _update_actions(self):
        self._clear_actions()
        #TODO : use _CremeModel.selection_label instead of 'Select'
        self._add_action('add', _(u'Select'), is_list_action=True)

        if self._q_filter is not None and self._create_action_url is None:
            return

        user = self._user

        if user is not None:
            self._add_create_action(user)

    def _value_to_jsonifiable(self, value):
        if not value:
            return []

        if value and isinstance(value[0], (int, long)):
            if self._entity_queryset(self.model, self.q_filter_query).filter(pk__in=value).count() < len(value):
                raise ValueError("One or more entities with ids [%s] doesn't exists." % ', '.join(str(v) for v in value))

            return value

        return list(map(super(MultiCreatorEntityField, self)._value_to_jsonifiable, value))

    def _value_from_unjsonfied(self, data):
        entities = []

        for entry in data:
            if not isinstance(entry, int):
                raise ValidationError(self.error_messages['invalidtype'], code='invalidtype')

            entity = self._clean_entity_from_model(self.model, entry, self.q_filter_query)

            if entity is None:
                raise ValidationError(self.error_messages['doesnotexist'], code='doesnotexist')

            entities.append(entity)

        if not entities:
            return self._return_list_or_raise(self.entities)

        return entities


#class _EntityField(Field):
    #"""
        #Base class for CremeEntityField and MultiCremeEntityField,
        #not really usable elsewhere avoid using it
    #"""
    #widget = ListViewWidget
    #default_error_messages = {
        #'invalid_choice': _(u"Select a valid choice. %(value)s is not an available choice."),
    #}

    #def __init__(self, model=None, q_filter=None, separator=',', *args, **kwargs):
        #super(_EntityField, self).__init__(*args, **kwargs)
        #self.model     = model
        #self.q_filter  = q_filter
        #self.o2m       = None
        #self.separator = separator

    #@property
    #def model(self):
        #return self._model

    #@model.setter
    #def model(self, model):
        #self._model = self.widget.model = model

    #@property
    #def q_filter(self):
        #return self._q_filter

    #@q_filter.setter
    #def q_filter(self, q_filter):
        #self._q_filter = self.widget.q_filter = q_filter

    #@property
    #def o2m(self):
        #return self._o2m

    #@o2m.setter
    #def o2m(self, o2m):
        #self._o2m = self.widget.o2m = o2m

    #@property
    #def separator(self):
        #return self._separator

    #@separator.setter
    #def separator(self, separator):
        #self._separator = self.widget.separator = separator

    #def clean(self, value):
        #value = super(_EntityField, self).clean(value)

        #if not value:
            #return None

        #if isinstance(value, basestring):
            #if self.separator in value:#In case of the widget doesn't make a 'good clean'
                #value = [v for v in value.split(self.separator) if v]
            #else:
                #value = [value]

        #try:
            #clean_ids = [int(v) for v in value]
        #except ValueError:
            #raise ValidationError(self.error_messages['invalid_choice'] % {'value': value})

        #return clean_ids


#class CremeEntityField(_EntityField):
    #"""
         #An input with comma (or anything) separated primary keys
         #clean method return a model instance
    #"""
    #default_error_messages = {
        #'doesnotexist': _(u"This entity doesn't exist."),
    #}

    #def __init__(self, model=CremeEntity, q_filter=None, *args, **kwargs):
        #super(CremeEntityField, self).__init__(model=model, q_filter=q_filter, *args, **kwargs)
        #self.o2m = 1

        #warnings.warn("CremeEntityField class is deprecated; use CreatorEntityField instead",
                      #DeprecationWarning
                     #)

    #def clean(self, value):
        #clean_id = super(CremeEntityField, self).clean(value)
        #if not clean_id:
            #return None

        #if len(clean_id) > 1:
            #raise ValidationError(self.error_messages['invalid_choice'] % {'value': value})

        #qs = self.model.objects.filter(is_deleted=False)

        #if self.q_filter is not None:
            #qs = qs.filter(get_q_from_dict(self.q_filter))

        #try:
            #return qs.get(pk=clean_id[0])
        #except self.model.DoesNotExist:
            #if self.required:
                #raise ValidationError(self.error_messages['doesnotexist'])


#class MultiCremeEntityField(_EntityField):
    #"""
         #An input with comma (or anything) separated primary keys
         #clean method return a list of real model instances
    #"""
    #def __init__(self, model=CremeEntity, q_filter=None, *args, **kwargs):
        #super(MultiCremeEntityField, self).__init__(model=model, q_filter=q_filter, *args, **kwargs)
        #self.o2m = 0

        #warnings.warn("MultiCremeEntityField class is deprecated; use MultiCreatorEntityField instead",
                      #DeprecationWarning
                     #)

    #def clean(self, value):
        #cleaned_ids = super(MultiCremeEntityField, self).clean(value)

        #if not cleaned_ids:
            #return []

        #qs = self.model.objects.filter(is_deleted=False, pk__in=cleaned_ids)

        #if self.q_filter is not None:
            #qs = qs.filter(get_q_from_dict(self.q_filter))

        #entities = list(qs)

        #if len(entities) != len(cleaned_ids):
            #raise ValidationError(self.error_messages['invalid_choice'] % {
                                        #'value': ', '.join(str(val) for val in value),
                                   #}
                                 #)

        #return entities


class FilteredEntityTypeField(JSONField):
    default_error_messages = {
        'ctyperequired':   _(u'The content type is required.'),
        'ctypenotallowed': _(u'This content type is not allowed.'), #TODO: factorise
        'invalidefilter':  _(u'This filter is invalid.'),
    }
    value_type = dict

    def __init__(self, ctypes=None, empty_label=None, *args, **kwargs):
        """Constructor.
        @param ctypes Allowed types.
                        - None : all CremeEntity types.
                        - Sequence of ContentType IDs / instances.
        """
        super(FilteredEntityTypeField, self).__init__(*args, **kwargs)
        self._empty_label = empty_label #TODO: setter property ??
        self.ctypes = ctypes
        self.user = None

    def __deepcopy__(self, memo): # TODO: move to JSONField ?? (some JSON will never have this problem but...)
        # NB: we force to create a 'cleaned' widget when instancing a form.
        #     The 'ctypes' property should be called when the form is instanced
        #     (because the list of entities can be empty if the form class is built too soon).
        result = super(FilteredEntityTypeField, self).__deepcopy__(memo)
        result.widget = result._create_widget()

        return result

    def _build_empty_value(self):
        return None, None

    def _clean_ctype(self, ctype_pk):
#        for ct in self._ctypes:
        for ct in self.ctypes:
            if ctype_pk == ct.id:
                return ct

    @property
    def ctypes(self):
        #return self._ctypes
        return self._ctypes or list(creme_entity_content_types())

    @ctypes.setter
    def ctypes(self, ctypes):
#        if ctypes is None:
#            ctypes = list(creme_entity_content_types())
#        else:
        if ctypes is not None:
            ctypes = [ct_or_ctid if isinstance(ct_or_ctid, ContentType) else
                      ContentType.objects.get_for_id(ct_or_ctid)
                        for ct_or_ctid in ctypes
                     ]

        self._ctypes = ctypes

        self._build_widget()

    def _create_widget(self):
        choices = []
        if self._empty_label is not None:
            choices.append((0, unicode(self._empty_label))) #TODO: improve widget to do not make a request for '0'

#        choices.extend(build_ct_choices(self._ctypes))
        choices.extend(build_ct_choices(self.ctypes))

        return FilteredEntityTypeWidget(choices)

    def _value_from_unjsonfied(self, data):
        clean_value = self.clean_value
        ctype_pk = clean_value(data, 'ctype',  int, required=False)

        if not ctype_pk:
            if self.required:
                raise ValidationError(self.error_messages['ctyperequired'],
                                      code='ctyperequired',
                                     )

            return self._build_empty_value()

        ct = self._clean_ctype(ctype_pk)
        if ct is None:
            raise ValidationError(self.error_messages['ctypenotallowed'],
                                  code='ctypenotallowed',
                                 )

        efilter_pk = clean_value(data, 'efilter',  str, required=False)
        if not efilter_pk:  #TODO: self.filter_required ???
            efilter = None
        else:
            try:
                if self.user:
                    efilter = EntityFilter.get_for_user(self.user, ct) \
                                          .get(pk=efilter_pk)
                else:
                    warnings.warn("FilteredEntityTypeField.clean(): 'user' attribute has not been set (so privacy cannot be checked)",
                                  DeprecationWarning
                                 )

                    efilter = EntityFilter.objects.get(entity_type=ct, pk=efilter_pk)
            except EntityFilter.DoesNotExist:
                raise ValidationError(self.error_messages['invalidefilter'],
                                      code='invalidefilter',
                                     )

        return ct, efilter

    def _value_to_jsonifiable(self, value):
        return {'ctype': value[0], 'efilter': value[1]}


class ListEditionField(Field):
    """A field to allow the user to edit/delete a list of strings.
    It returns a list with the same order:
    * deleted elements are replaced by None.
    * modified elements are replaced by the new value.
    """
    widget = ListEditionWidget
    default_error_messages = {}

    def __init__(self, content=(), only_delete=False, *args, **kwargs):
        """
        @param content Sequence of strings
        @param only_delete Can only delete elements, not edit them.
        """
        super(ListEditionField, self).__init__(*args, **kwargs)
        self.content = content
        self.only_delete = only_delete

    @property
    def content(self):
        return self._content

    @content.setter
    def content(self, content):
        self._content = content
        self.widget.content = content

    @property
    def only_delete(self):
        return self._only_delete

    @only_delete.setter
    def only_delete(self, only_delete):
        self._only_delete = only_delete
        self.widget.only_delete = only_delete


class AjaxChoiceField(ChoiceField):
    """
        Same as ChoiceField but bypass the choices validation due to the ajax filling
    """
    def clean(self, value):
        """
        Validates that the input is in self.choices.
        """
#        value = super(ChoiceField, self).clean(value)

        is_value_empty = value in EMPTY_VALUES

        if self.required and is_value_empty:
            raise ValidationError(self.error_messages['required'], code='required')

        if is_value_empty:
            value = u''

        return smart_unicode(value)


class AjaxMultipleChoiceField(MultipleChoiceField):
    """
        Same as MultipleChoiceField but bypass the choices validation due to the ajax filling
    """
    def clean(self, value):
        """
        Validates that the input is a list or tuple.
        """
        not_value = not value
        if self.required and not_value:
            raise ValidationError(self.error_messages['required'], code='required')
        elif not self.required and not_value:
            return []

        if not isinstance(value, (list, tuple)):
            raise ValidationError(self.error_messages['invalid_list'],
                                  code='invalid_list',
                                 )

        return [smart_unicode(val) for val in value]


class AjaxModelChoiceField(ModelChoiceField):
    """
        Same as ModelChoiceField but bypass the choices validation due to the ajax filling
    """
    def clean(self, value):
#        Field.clean(self, value)

        if value in EMPTY_VALUES:
            return None

        try:
            key   = self.to_field_name or 'pk'
            value = self.queryset.model._default_manager.get(**{key: value})
        except self.queryset.model.DoesNotExist:
            raise ValidationError(self.error_messages['invalid_choice'],
                                  code='invalid_choice',
                                 )

        return value


class CremeTimeField(TimeField):
    widget = TimeWidget


class CremeDateField(DateField):
    widget = CalendarWidget


class CremeDateTimeField(DateTimeField):
    widget = CalendarWidget


class MultiEmailField(Field):
    #Original code at http://docs.djangoproject.com/en/1.3/ref/forms/validation/#form-field-default-cleaning
    widget = Textarea

    def __init__(self, sep="\n", *args, **kwargs):
        super(MultiEmailField, self).__init__(*args, **kwargs)
        self.sep = sep

    def to_python(self, value):
        "Normalize data to a list of strings."

        # Return an empty list if no input was given.
        if not value:
            return []
        return [v for v in value.split(self.sep) if v]#Remove empty values but the validation is more flexible

    def validate(self, value):
        "Check if value consists only of valid emails."

        # Use the parent's handling of required fields, etc.
        super(MultiEmailField, self).validate(value)

        for email in value:
            validate_email(email)


class DatePeriodField(MultiValueField):
    widget = DatePeriodWidget

    def __init__(self, *args, **kwargs):
        choices = kwargs.pop("choices", None)
        super(DatePeriodField, self).__init__((ChoiceField(), IntegerField(min_value=1)),
                                              *args, **kwargs
                                             )
        #TODO: 'choices' property
        self.fields[0].choices = self.widget.choices = list(date_period_registry.choices(choices=choices))

    def compress(self, data_list):
        if data_list:
            return data_list[0], data_list[1]

        return u'', u''

    def clean(self, value):
        period_name, period_value = super(DatePeriodField, self).clean(value)

        return date_period_registry.get_period(period_name, period_value)


class DateRangeField(MultiValueField):
    """A field which returns a creme_core.utils.DateRange.
    Commonly used with a DateRangeWidget.
    eg:
        #Use DateRangeWidget with defaults params
        DateRangeField(label=_(u'Date range'))

        #Render DateRangeWidget as ul/li
        DateRangeField(label=_(u'Date range'), widget=DateRangeWidget(attrs={'render_as': 'ul'}))

        #Render DateRangeWidget as a table
        DateRangeField(label=_(u'Date range'), widget=DateRangeWidget(attrs={'render_as': 'table'}))
    """
    widget = DateRangeWidget
    default_error_messages = {
        'customized_empty': _(u'If you select «customized» you have to specify a start date and/or an end date.'),
        'customized_invalid': _(u'Start date has to be before end date.'),
    }

#    def __init__(self, render_as="table", required=True, *args, **kwargs):
    def __init__(self, render_as="table", *args, **kwargs):
#        self.ranges     = ChoiceField(choices=chain([(u'', _(u'Customized'))], date_range_registry.choices()))
#        self.start_date = DateField()
#        self.end_date   = DateField()
        # TODO: are these attributes useful ??
        self.ranges     = ChoiceField(choices=chain([(u'', _(u'Customized'))],
                                                    date_range_registry.choices(),
                                                   ),
                                      required=False,
                                     )
        self.start_date = DateField(required=False)
        self.end_date   = DateField(required=False)
        self.render_as  = render_as

#        fields = self.ranges, self.start_date, self.end_date
#        super(DateRangeField, self).__init__(fields, required=required, *args, **kwargs)
        super(DateRangeField, self).__init__(fields=(self.ranges,
                                                     self.start_date,
                                                     self.end_date,
                                                    ),
                                             require_all_fields=False, *args, **kwargs
                                            )

    def compress(self, data_list):
        if data_list:
            return data_list[0], data_list[1], data_list[2]
        return u'', u'', u''

    def clean(self, value):
#        # MultiValueField manages "required" for all fields together
#        # thought we need to manage them independently (range or end_date
#        # can be an empty string) so we have to hook it.
#        previous_required = self.required
#        self.required = False
        range_name, start, end = super(DateRangeField, self).clean(value)
#        self.required = previous_required

        if range_name == "":
            if not start and not end and self.required:
                raise ValidationError(self.error_messages['customized_empty'],
                                      code='customized_empty',
                                     )

            if start and end and start > end:
                raise ValidationError(self.error_messages['customized_invalid'],
                                      code='customized_invalid',
                                     )

        return date_range_registry.get_range(range_name, start, end)

    def widget_attrs(self, widget):
        return {'render_as': self.render_as}


class ColorField(RegexField):
    """A Field which handle html colors (e.g: #F2FAB3) without '#' """
    regex  = compile_re(r'^([0-9a-fA-F]){6}$')
    widget = ColorPickerWidget
    default_error_messages = {
        'invalid': _(u'Enter a valid value (eg: DF8177).'),
    }

    def __init__(self, *args, **kwargs):
        super(ColorField, self).__init__(self.regex, max_length=6, min_length=6, *args, **kwargs)

    def clean(self, value):
        return super(ColorField, self).clean(value).upper()


class DurationField(MultiValueField):
    widget = DurationWidget
    default_error_messages = {
        'invalid': _(u'Enter a whole number.'),
        'min_value': _(u'Ensure this value is greater than or equal to %(limit_value)s.'),
    }

    def __init__(self, *args, **kwargs):
        self.hours   = IntegerField(min_value=0)
        self.minutes = IntegerField(min_value=0)
        self.seconds = IntegerField(min_value=0)

        fields = self.hours, self.minutes, self.seconds

        super(DurationField, self).__init__(fields=fields, *args, **kwargs)

    def compress(self, data_list):
        if data_list:
            return data_list[0], data_list[1], data_list[2]
        return u'', u'', u''

    def clean(self, value):
        hours, minutes, seconds = super(DurationField, self).clean(value)
        hours   = hours   or 0
        minutes = minutes or 0
        seconds = seconds or 0
        return ':'.join([str(hours), str(minutes), str(seconds)])


class ChoiceOrCharField(MultiValueField):
    widget = ChoiceOrCharWidget

    default_error_messages = {
        'invalid_other': _(u'Enter a value for "Other" choice.'),
    }

    def __init__(self, choices=(), *args, **kwargs):
        """@param choices Sequence of tuples (id, value).
                          BEWARE: id should not be a null value (like '', 0, etc..).
        """
        self.choice_field = choice_field = ChoiceField()
#        fields = (choice_field, CharField())
#        super(ChoiceOrCharField, self).__init__(fields=fields, *args, **kwargs)
        super(ChoiceOrCharField, self).__init__(fields=(choice_field, CharField(required=False)),
                                                require_all_fields=False,
                                                *args, **kwargs
                                               )
#        self.original_required = self.required
#        self.required = False #MultiValueField.clean does not used the 'required' attr of internal fields
#                              #so the CharField could not return ''if self.required was True

        self.choices = choices

    @property
    def choices(self):
        return self._choices

    @choices.setter
    def choices(self, value):
        """See ChoiceField._set_choices()"""
        choices = [(0, _('Other'))]
        choices.extend(value)
        self._choices = self.choice_field.choices = self.widget.choices = choices

    def compress(self, data_list):
        index = None
        strval = None

        if data_list:
            index = data_list[0]

            if index == '0':
                index = 0
                strval = data_list[1]
            elif index:
                index, strval = find_first(self.choices, lambda item: str(item[0]) == index)

        return (index, strval)

    def clean(self, value):
        value = super(ChoiceOrCharField, self).clean(value)

#        index = value[0]

#        if self.original_required and index is None:
#            raise ValidationError(self.error_messages['required'], code='required')

#        if index == 0 and not value[1]:
        if value[0] == 0 and not value[1]:
            raise ValidationError(self.error_messages['invalid_other'],
                                  code='invalid_other',
                                 )

        return value


class CTypeChoiceField(Field):
    "A ChoiceField whose choices are a ContentType instances."
    widget = Select
    default_error_messages = {
        'invalid_choice': _(u'Select a valid choice. That choice is not one of'
                            u' the available choices.'),
    }

    #TODO: ctypes_or_models ??
    def __init__(self, ctypes=(), empty_label=u"---------",
                 required=True, widget=None, label=None, initial=None,
                 help_text=None, to_field_name=None, limit_choices_to=None,
                 *args, **kwargs):
        super(CTypeChoiceField, self).__init__(required, widget, label, initial, help_text,
                                               *args, **kwargs
                                              )
        self.empty_label = empty_label
        self.ctypes = ctypes

    def __deepcopy__(self, memo):
        result = super(CTypeChoiceField, self).__deepcopy__(memo)
        result._ctypes = deepcopy(self._ctypes, memo)
        return result

    @property
    def ctypes(self):
        return self._ctypes

    @ctypes.setter
    def ctypes(self, ctypes):
        self._ctypes = ctypes = list(ctypes)
        choices = self._build_empty_choice(self._build_ctype_choices(ctypes))

        self.widget.choices = choices

    def _build_empty_choice(self, choices):
        if not self.required:
            return [('', self.empty_label)] + choices

        return choices

    def _build_ctype_choices(self, ctypes):
        return build_ct_choices(ctypes)

    def to_python(self, value):
        if value in EMPTY_VALUES:
            return None

        try:
            ct_id = int(value)

            for ctype in self._ctypes:
                if ctype.id == ct_id:
                    return ctype
        except ValueError:
            pass

        raise ValidationError(self.error_messages['invalid_choice'],
                              code='invalid_choice',
                             )


class MultiCTypeChoiceField(CTypeChoiceField):
    widget = UnorderedMultipleChoiceWidget()

    def _build_ctype_choices(self, ctypes):
        from ..utils.unicode_collation import collator
        from ..registry import creme_registry

        Choice = UnorderedMultipleChoiceWidget.Choice
        get_app = creme_registry.get_app

        choices = [(Choice(ct.id, help=_(get_app(ct.app_label).verbose_name)), unicode(ct)) for ct in ctypes]
        sort_key = collator.sort_key
        choices.sort(key=lambda k: sort_key(k[1]))

        return choices

    def _build_empty_choice(self, choices):
        return choices

    def to_python(self, value):
        ctypes = []

        if value not in EMPTY_VALUES:
            to_python = super(MultiCTypeChoiceField, self).to_python
            ctypes.extend(to_python(ct_id) for ct_id in value)

        return ctypes


class EntityCTypeChoiceField(CTypeChoiceField):
    def __init__(self, ctypes=None, *args, **kwargs):
        ctypes = ctypes or creme_entity_content_types()
        super(EntityCTypeChoiceField, self).__init__(ctypes=ctypes, *args, **kwargs)


class MultiEntityCTypeChoiceField(MultiCTypeChoiceField):
    def __init__(self, ctypes=None, *args, **kwargs):
        ctypes = ctypes or creme_entity_content_types()
        super(MultiEntityCTypeChoiceField, self).__init__(ctypes=ctypes, *args, **kwargs)
