# -*- coding: utf-8 -*-

################################################################################
#    Creme is a free/open-source Customer Relationship Management software
#    Copyright (C) 2009-2018  Hybird
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

from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.forms import ModelMultipleChoiceField, CharField
from django.utils.translation import ugettext_lazy as _, ugettext

from ..models import CremePropertyType, CremeProperty
from ..utils import entities2unicode
from .base import CremeForm
from .widgets import Label


class _AddPropertiesForm(CremeForm):
    types = ModelMultipleChoiceField(label=_(u'Type of property'),
                                     queryset=CremePropertyType.objects.none(),
                                    )

    def _create_properties(self, entities, ptypes):
        property_get_or_create = CremeProperty.objects.get_or_create

        for entity in entities:
            for ptype in ptypes:
                property_get_or_create(type=ptype, creme_entity=entity)


class AddPropertiesForm(_AddPropertiesForm):
    def __init__(self, entity, *args, **kwargs):
        # We need this entity in super constructor when post_init_callback is called.
        # TODO: Add unit tests for this !
        self.entity = entity
        super(AddPropertiesForm, self).__init__(*args, **kwargs)

        # TODO: move queryset to a CremePropertyType method ??
        excluded = CremeProperty.objects.filter(creme_entity=entity).values_list('type', flat=True)
        self.fields['types'].queryset = CremePropertyType.objects.filter(Q(subject_ctypes=entity.entity_type_id) |
                                                                         Q(subject_ctypes__isnull=True)
                                                                        ) \
                                                                 .exclude(pk__in=excluded)

    def save(self):
        self._create_properties([self.entity], self.cleaned_data['types'])


class AddPropertiesBulkForm(_AddPropertiesForm):
    entities_lbl = CharField(label=_(u"Related entities"), widget=Label(), required=False)

    def __init__(self, model, entities, forbidden_entities, *args, **kwargs):
        super(AddPropertiesBulkForm, self).__init__(*args, **kwargs)
        self.entities = entities
        fields = self.fields
        ct = ContentType.objects.get_for_model(model)

        fields['types'].queryset = CremePropertyType.get_compatible_ones(ct)  # TODO: Sort?
        fields['entities_lbl'].initial = entities2unicode(entities, self.user) if entities else ugettext(u'NONE !')

        if forbidden_entities:
            fields['bad_entities_lbl'] = CharField(label=ugettext(u"Uneditable entities"),
                                                   widget=Label, required=False,
                                                   initial=entities2unicode(forbidden_entities, self.user),
                                                  )

    def save(self):
        self._create_properties(self.entities, self.cleaned_data['types'])
