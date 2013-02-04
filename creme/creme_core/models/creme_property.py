# -*- coding: utf-8 -*-

################################################################################
#    Creme is a free/open-source Customer Relationship Management software
#    Copyright (C) 2009-2012  Hybird
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

from django.db.models import CharField, ForeignKey, ManyToManyField, BooleanField, Q
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType

from creme_core.signals import pre_merge_related
from base import CremeModel
from entity import CremeEntity


class CremePropertyType(CremeModel):
    id             = CharField(primary_key=True, max_length=100)
    text           = CharField(max_length=200, unique=True)
    subject_ctypes = ManyToManyField(ContentType, blank=True, null=True, related_name='subject_ctypes_creme_property_set')
    is_custom      = BooleanField(default=False)

    def __unicode__(self):
        return self.text

    class Meta:
        app_label = 'creme_core'
        verbose_name = _(u'Type of property')
        verbose_name_plural = _(u'Types of property')

    def delete(self):
        #self.property_i18n_set.all().delete()
        CremeProperty.objects.filter(type=self).delete()
        super(CremePropertyType, self).delete()

    @staticmethod
    def create(str_pk, text, subject_ctypes=(), is_custom=False, generate_pk=False):
        """Helps the creation of new CremePropertyType.
        @param subject_ctypes Sequence of CremeEntity classes/ContentType objects.
        @param generate_pk If True, str_pk is used as prefix to generate pk.
        """
        if not generate_pk:
            from creme_core.utils import create_or_update
            property_type = create_or_update(CremePropertyType, str_pk, text=text, is_custom=is_custom)
        else:
            from creme_core.utils.id_generator import generate_string_id_and_save
            property_type = CremePropertyType(text=text, is_custom=is_custom)
            generate_string_id_and_save(CremePropertyType, [property_type], str_pk)

        #property_type.property_i18n_set.all().delete()
        #CremePropertyText_i18n.objects.create(property_type_id=property_type.id, language_code='FRA', i18n_text=text)

        get_ct = ContentType.objects.get_for_model
        property_type.subject_ctypes = [(model if isinstance(model, ContentType) else get_ct(model)) for model in subject_ctypes]

        return property_type

    @staticmethod
    def get_compatible_ones(ct):
        return CremePropertyType.objects.filter(Q(subject_ctypes=ct) | Q(subject_ctypes__isnull=True))

#class CremePropertyText_i18n(CremeModel):
    #property_type = ForeignKey(CremePropertyType, related_name='property_i18n_set')
    #language_code = CharField(max_length=5)
    #i18n_text     = CharField(max_length=100)

    #class Meta:
        #app_label = 'creme_core'


class CremeProperty(CremeModel):
    type         = ForeignKey(CremePropertyType)
    creme_entity = ForeignKey(CremeEntity, related_name="properties") #related_name="creme_property_set" ??

    class Meta:
        app_label = 'creme_core'
        verbose_name = _(u'Property')
        verbose_name_plural = _(u'Properties')

    def __unicode__(self):
        return unicode(self.type)

    def get_related_entity(self): #for generic views
        return self.creme_entity


def _handle_merge(sender, other_entity, **kwargs):
    sender_id = sender.id
    prop_filter = sender.properties.filter

    for prop in other_entity.properties.all():
        if prop_filter(creme_entity=sender_id, type=prop.type_id).exists():
            prop.delete()
        else:
            prop.creme_entity = sender
            prop.save()


pre_merge_related.connect(_handle_merge, dispatch_uid='creme_core-properties_handle_merge')
