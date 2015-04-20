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

from future_builtins import filter
import warnings

from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.db.models import CharField, TextField, ForeignKey, PositiveIntegerField
from django.db.models.signals import post_delete
from django.utils.translation import ugettext_lazy as _

from creme.creme_core.models import CremeEntity, CremeModel
from creme.creme_core.signals import pre_merge_related


class Address(CremeModel):
    name       = CharField(_(u"Name"), max_length=100, blank=True, null=True)
    address    = TextField(_(u"Address"), blank=True, null=True)
    po_box     = CharField(_(u"PO box"), max_length=50, blank=True, null=True)
    zipcode    = CharField(_(u"Zip code"), max_length=100, blank=True, null=True)
    city       = CharField(_(u"City"), max_length=100, blank=True, null=True)
    department = CharField(_(u"Department"), max_length=100, blank=True, null=True)
    state      = CharField(_(u"State"), max_length=100, blank=True, null=True)
    country    = CharField(_(u"Country"), max_length=40, blank=True, null=True)

    content_type = ForeignKey(ContentType, related_name="object_set", editable=False).set_tags(viewable=False)
    object_id    = PositiveIntegerField(editable=False).set_tags(viewable=False)
    owner        = GenericForeignKey(ct_field="content_type", fk_field="object_id")

    class Meta:
        app_label = 'persons'
        verbose_name = _(u'Address')
        verbose_name_plural = _(u'Addresses')

    def __unicode__(self):
        s = u' '.join(filter(None, [self.address, self.zipcode, self.city, self.department]))

        if not s:
            s = u' '.join(filter(None, [self.po_box, self.state, self.country]))

        return s

    def get_edit_absolute_url(self):
        return '/persons/address/edit/%s' % self.id

    def get_related_entity(self): #for generic views
        return self.owner

    _INFO_FIELD_NAMES = ('name', 'address', 'po_box', 'zipcode', 'city', 'department', 'state', 'country')

    def __nonzero__(self): #used by forms to detect empty addresses
        return any(fvalue for fname, fvalue in self.info_fields)

    def _get_info_fields(self):
        warnings.warn("Address._get_info_fields() method is deprecated ; use Address.info_fields instead",
                      DeprecationWarning
                     )

        return self.info_fields

    def clone(self, entity):
        """Returns a new cloned (saved) address for a (saved) entity"""
        return Address.objects.create(object_id=entity.id,
                                      content_type=ContentType.objects.get_for_model(entity),
                                      **dict(self.info_fields)
                                     )

    @property
    def info_fields(self):
        for fname in self._INFO_FIELD_NAMES:
            yield fname, getattr(self, fname)


#TODO: with a real ForeignKey can not we remove these handlers ??
def _dispose_addresses(sender, instance, **kwargs):
    Address.objects.filter(object_id=instance.id).delete()

def _handle_merge(sender, other_entity, **kwargs):
    #TODO: factorise with blocks.OtherAddressBlock.detailview_display()
    excluded_pk = filter(None, [other_entity.billing_address_id, other_entity.shipping_address_id])

    for address in Address.objects.filter(object_id=other_entity.id).exclude(pk__in=excluded_pk):
        address.owner = sender
        address.save()

post_delete.connect(_dispose_addresses, sender=CremeEntity)
pre_merge_related.connect(_handle_merge)
