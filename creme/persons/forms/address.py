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

from creme.creme_core.forms import CremeModelForm

from ..models import Address


class AddressForm(CremeModelForm):
    class Meta(CremeModelForm.Meta):
        model = Address

    def __init__(self, entity, *args, **kwargs):
        super(AddressForm, self).__init__(*args, **kwargs)
        self._entity = entity

    def save(self, *args, **kwargs):
        self.instance.owner = self._entity
        return super(AddressForm, self).save(*args, **kwargs)


class _FieldAddressForm(AddressForm):
    field_name = 'OVERLOAD'

    def save(self, *args, **kwargs):
        entity = self._entity
        address = super(_FieldAddressForm, self).save(*args, **kwargs)

        setattr(entity, self.field_name, address)
        entity.save() #TODO: with django 1.5: save only one field

        return address


class BillingAddressForm(_FieldAddressForm):
    field_name = 'billing_address'


class ShippingAddressForm(_FieldAddressForm):
    field_name = 'shipping_address'
