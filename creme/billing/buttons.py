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

from django.utils.translation import ugettext_lazy as _

from creme.creme_core.gui.button_menu import Button

from creme.persons import get_organisation_model, get_contact_model
#from creme.persons.models import Contact, Organisation

from . import get_invoice_model, get_quote_model, get_sales_order_model
from .models import Base #Quote, Invoice, SalesOrder


Invoice      = get_invoice_model()
Quote        = get_quote_model()
SalesOrder   = get_sales_order_model()


class GenerateInvoiceNumberButton(Button):
    id_           = Button.generate_id('billing', 'generate_invoice_number')
    verbose_name  = _(u'Generate the number of the Invoice')
    template_name = 'billing/templatetags/button_generate_invoice_number.html'

    def get_ctypes(self):
#        from .models import Invoice
        return (Invoice,)

    def has_perm(self, context):
        return context['user'].has_perm_to_change(context['object'])

    def ok_4_display(self, entity):
        return not bool(entity.number)


class _AddBillingDocumentButton(Button):
    template_name   = 'billing/templatetags/button_add_billing_document.html'
    model_to_create = Base #overload
    url_name        = 'OVERLOADME'

    def get_ctypes(self):
        #return (Organisation, Contact)
        return (get_organisation_model(), get_contact_model())

    def has_perm(self, context):
        return context['user'].has_perm_to_create(self.model_to_create)

#    def ok_4_display(self, entity):
##        self.__managed_orga = Organisation.get_all_managed_by_creme()
#        self.__managed_orga = get_organisation_model().get_all_managed_by_creme()
#        return bool(self.__managed_orga)

    def render(self, context):
#        context['managed_orga'] = self.__managed_orga
        context['verbose_name'] = self.verbose_name
#        context['which_document'] = self.model_to_create.__name__.lower()
#        context['become_url'] = self.become_url % context['object'].id
        context['model_vname'] = self.model_to_create._meta.verbose_name
        context['url_name'] = self.url_name

        return super(_AddBillingDocumentButton, self).render(context)


class AddInvoiceButton(_AddBillingDocumentButton):
    model_to_create = Invoice
    id_             = Button.generate_id('billing', 'add_invoice')
    verbose_name    = _(u'Add a related invoice')
    permission      = 'billing.add_invoice'
#    become_url      = "/billing/invoice/add/%s"
    url_name      = 'billing__create_related_invoice'


class AddSalesOrderButton(_AddBillingDocumentButton):
    model_to_create = SalesOrder
    id_             = Button.generate_id('billing', 'add_salesorder')
    verbose_name    = _(u'Add a related sales order')
    permission      = 'billing.add_salesorder'
#    become_url      = "/billing/sales_order/add/%s"
    url_name        = 'billing__create_related_order'

class AddQuoteButton(_AddBillingDocumentButton):
    model_to_create = Quote
    id_             = Button.generate_id('billing', 'add_quote')
    verbose_name    = _(u'Add a related quote')
    permission      = 'billing.add_quote'
#    become_url      = "/billing/quote/add/%s"
    url_name        = 'billing__create_related_quote'


generate_invoice_number_button  = GenerateInvoiceNumberButton()
add_related_quote               = AddQuoteButton()
add_related_salesorder          = AddSalesOrderButton()
add_related_invoice             = AddInvoiceButton()

button_list = (
        generate_invoice_number_button,
        add_related_quote,
        add_related_salesorder,
        add_related_invoice,
    )
