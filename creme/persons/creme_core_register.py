# -*- coding: utf-8 -*-

################################################################################
#    Creme is a free/open-source Customer Relationship Management software
#    Copyright (C) 2009-2011  Hybird
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

from django.utils.translation import ugettext_lazy as _

from creme_core.registry import creme_registry
from creme_core.gui import (creme_menu, button_registry, block_registry, icon_registry,
                            quickforms_registry, csv_form_registry, bulk_update_registry)

from persons.models import Contact, Organisation
from persons.buttons import (become_customer_button, become_prospect_button, become_suspect_button,
                             become_inactive_button, become_supplier_button, add_linked_contact_button)
from persons.blocks import block_list, ContactBlock, OrganisationBlock
from persons.forms.quick import ContactQuickForm, OrganisationQuickForm
from persons.forms.csv_import import get_csv_form_builder


creme_registry.register_entity_models(Contact, Organisation)
creme_registry.register_app('persons', _(u'Accounts and Contacts'), '/persons')

reg_item = creme_menu.register_app('persons', '/persons/').register_item
reg_item('/persons/',                 _(u'Portal'),                              'persons')
reg_item('/persons/contacts',         _(u'All contacts'),                        'persons')
reg_item('/persons/leads_customers',  _(u'My customers / prospects / suspects'), 'persons')
reg_item('/persons/contact/add',      _(u'Add a contact'),                       'persons.add_contact')
reg_item('/persons/organisations',    _(u'All organisations'),                   'persons')
reg_item('/persons/organisation/add', _(u'Add an organisation'),                 'persons.add_organisation')


button_registry.register(become_customer_button, become_prospect_button, become_suspect_button,
                         become_inactive_button, become_supplier_button, add_linked_contact_button)

block_registry.register_4_model(Contact,      ContactBlock())
block_registry.register_4_model(Organisation, OrganisationBlock())
block_registry.register(*block_list)

reg_icon = icon_registry.register
reg_icon(Contact,      'images/contacts_%(size)s.png')
reg_icon(Organisation, 'images/organisation_%(size)s.png')

reg_qform = quickforms_registry.register
reg_qform(Contact,      ContactQuickForm)
reg_qform(Organisation, OrganisationQuickForm)

register_csv_form = csv_form_registry.register
register_csv_form(Contact,      get_csv_form_builder)
register_csv_form(Organisation, get_csv_form_builder)

bulk_update_registry.register(
    (Contact,      ['is_user', 'billing_address', 'shipping_address']),
    (Organisation, ['siren', 'billing_address', 'shipping_address']),
)