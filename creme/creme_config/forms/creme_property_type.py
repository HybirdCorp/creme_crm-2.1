# -*- coding: utf-8 -*-

################################################################################
#    Creme is a free/open-source Customer Relationship Management software
#    Copyright (C) 2009-2016  Hybird
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

from django.forms import CharField, BooleanField, ValidationError
from django.utils.translation import ugettext_lazy as _, ugettext

from creme.creme_core.models import CremePropertyType
from creme.creme_core.forms import CremeForm, MultiEntityCTypeChoiceField


class _CremePropertyTypeBaseForm(CremeForm):
    text           = CharField(label=_(u'Text'), help_text=_("For example: 'is pretty'"))
    is_copiable    = BooleanField(label=_(u'Is copiable'), initial=True, required=False,
                                  help_text=_(u'Are the properties with this type copied when an entity is cloned?'),
                                 )
    subject_ctypes = MultiEntityCTypeChoiceField(label=_(u'Related to types of entities'),
                                                 help_text=_(u'No selected type means that all types are accepted'),
                                                 required=False,
                                                )


class CremePropertyTypeAddForm(_CremePropertyTypeBaseForm):
    def clean_text(self):
        text = self.cleaned_data['text']

        if CremePropertyType.objects.filter(text=text).exists():  # TODO: unique constraint in model too ??
            raise ValidationError(ugettext(u"A property type with this name already exists"),
                                  code='duplicated_name',
                                 )

        return text

    def save(self):
        get_data = self.cleaned_data.get
        ptype = CremePropertyType.create('creme_config-userproperty',
                                         get_data('text'), get_data('subject_ctypes'),
                                         is_custom=True, generate_pk=True,
                                         is_copiable=get_data('is_copiable'),
                                        )
        super(CremePropertyTypeAddForm, self).save()

        return ptype


class CremePropertyTypeEditForm(_CremePropertyTypeBaseForm):
    def __init__(self, instance, *args, **kwargs):
        super(CremePropertyTypeEditForm, self).__init__(*args, **kwargs)

        self.instance = instance
        fields = self.fields

        fields['text'].initial           = instance.text
        fields['is_copiable'].initial    = instance.is_copiable
        fields['subject_ctypes'].initial = [ct.id for ct in instance.subject_ctypes.all()]

    def save(self):
        get_data = self.cleaned_data.get
        CremePropertyType.create(self.instance.id, get_data('text'),
                                 get_data('subject_ctypes'), is_custom=True,
                                 is_copiable=get_data('is_copiable'),
                                )
        super(CremePropertyTypeEditForm, self).save()
