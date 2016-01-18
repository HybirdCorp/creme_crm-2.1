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

from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _

from creme.creme_core.gui.block import SimpleBlock, QuerysetBlock
from creme.creme_core.models import Relation

from creme.persons import get_contact_model, get_organisation_model

from creme.products import get_product_model, get_service_model

from . import get_opportunity_model
from . import constants


Opportunity = get_opportunity_model()
Contact = get_contact_model()
Organisation = get_organisation_model()
Product = get_product_model()
Service = get_service_model()
_get_ct = ContentType.objects.get_for_model


class OpportunityBlock(SimpleBlock):
    template_name = 'creme_core/templatetags/block_object.html'
    dependencies  = (Opportunity, Relation)
    relation_type_deps = (constants.REL_OBJ_LINKED_QUOTE, )


class _LinkedStuffBlock(QuerysetBlock):
    # id_           = SET ME
    dependencies  = (Relation,)
    # relation_type_deps = SET ME
    # verbose_name  = SET ME
    # template_name = SET ME
    target_ctypes = (Opportunity,)

    _ct = _get_ct(Contact)  # Overload if needed

    def _get_queryset(self, entity):  # Overload
        pass

    def detailview_display(self, context):
        entity = context['object']

        return self._render(self.get_block_template_context(
                                context,
                                self._get_queryset(entity),
                                update_url='/creme_core/blocks/reload/%s/%s/' % (self.id_, entity.pk),
                                predicate_id=self.relation_type_deps[0],
                                ct=self._ct,
                               )
                           )


class LinkedContactsBlock(_LinkedStuffBlock):
    id_           = QuerysetBlock.generate_id('opportunities', 'linked_contacts')
    dependencies  = (Relation, Contact)
    relation_type_deps = (constants.REL_OBJ_LINKED_CONTACT, )
    verbose_name  = _(u'Linked Contacts')
    template_name = 'opportunities/templatetags/block_contacts.html'

    def _get_queryset(self, entity):
        return entity.get_contacts().select_related('civility')


class LinkedProductsBlock(_LinkedStuffBlock):
    id_           = QuerysetBlock.generate_id('opportunities', 'linked_products')
    dependencies  = (Relation, Product)
    relation_type_deps = (constants.REL_OBJ_LINKED_PRODUCT, )
    verbose_name  = _(u'Linked Products')
    template_name = 'opportunities/templatetags/block_products.html'

    _ct = _get_ct(Product)

    def _get_queryset(self, entity):
        return entity.get_products()


class LinkedServicesBlock(_LinkedStuffBlock):
    id_           = QuerysetBlock.generate_id('opportunities', 'linked_services')
    dependencies  = (Relation, Service)
    relation_type_deps = (constants.REL_OBJ_LINKED_SERVICE, )
    verbose_name  = _(u'Linked Services')
    template_name = 'opportunities/templatetags/block_services.html'

    _ct = _get_ct(Service)

    def _get_queryset(self, entity):
        return entity.get_services()


class ResponsiblesBlock(_LinkedStuffBlock):
    id_           = QuerysetBlock.generate_id('opportunities', 'responsibles')
    dependencies  = (Relation, Contact)
    relation_type_deps = (constants.REL_OBJ_RESPONSIBLE, )
    verbose_name  = _(u'Responsibles')
    template_name = 'opportunities/templatetags/block_responsibles.html'

    def _get_queryset(self, entity):
        return entity.get_responsibles().select_related('civility')


class TargettingOpportunitiesBlock(QuerysetBlock):
    id_           = QuerysetBlock.generate_id('opportunities', 'target_organisations')
    dependencies  = (Relation, Opportunity)
    relation_type_deps = (constants.REL_OBJ_TARGETS, )
    verbose_name  = _(u"Opportunities which target the organisation / contact")
    template_name = 'opportunities/templatetags/block_opportunities.html'
    target_ctypes = (Organisation, Contact)

    _ct = _get_ct(Opportunity)

    def detailview_display(self, context):
        entity = context['object']
        is_hidden = context['fields_configs'].get_4_model(Opportunity).is_fieldname_hidden

        return self._render(self.get_block_template_context(
                                context,
                                # TODO: filter deleted ??
                                Opportunity.objects.filter(relations__object_entity=entity.id,
                                                           relations__type=constants.REL_SUB_TARGETS,
                                                          ),
                                update_url='/creme_core/blocks/reload/%s/%s/' % (self.id_, entity.pk),
                                predicate_id=self.relation_type_deps[0],
                                ct=self._ct,
                                hidden_fields={fname
                                                for fname in ('estimated_sales', 'made_sales')
                                                    if is_hidden(fname)
                                              },
                               )
                           )


class OppTotalBlock(SimpleBlock):
    id_                 = SimpleBlock.generate_id('opportunities', 'total')
    dependencies        = (Opportunity, Relation)
    relation_type_deps  = (constants.REL_OBJ_LINKED_QUOTE,)
    verbose_name        = _(u'Total')
    template_name       = 'opportunities/templatetags/block_total.html'
    target_ctypes       = (Opportunity,)


class OppTargetBlock(SimpleBlock):
    id_           = SimpleBlock.generate_id('opportunities', 'target')
    dependencies  = (Opportunity, Organisation)
    verbose_name  = _(u'Target organisation')
    template_name = 'opportunities/templatetags/block_target.html'
    target_ctypes = (Opportunity,)


linked_contacts_block = LinkedContactsBlock()
linked_products_block = LinkedProductsBlock()
linked_services_block = LinkedServicesBlock()
responsibles_block    = ResponsiblesBlock()
total_block           = OppTotalBlock()
target_block          = OppTargetBlock()
targetting_opps_block = TargettingOpportunitiesBlock()

blocks_list = (
    linked_contacts_block,
    linked_products_block,
    linked_services_block,
    responsibles_block,
    total_block,
    target_block,
    targetting_opps_block,
)


if apps.is_installed('creme.billing'):
    from creme.billing import get_invoice_model, get_quote_model, get_sales_order_model

    Invoice    = get_invoice_model()
    Quote      = get_quote_model()
    SalesOrder = get_sales_order_model()

    class QuotesBlock(_LinkedStuffBlock):
        id_                = QuerysetBlock.generate_id('opportunities', 'quotes')
        dependencies       = (Relation, Quote)
        relation_type_deps = (constants.REL_OBJ_LINKED_QUOTE,)
        verbose_name       = _(u"Quotes linked to the opportunity")
        template_name      = 'opportunities/templatetags/block_quotes.html'

        _ct = _get_ct(Quote)

        def _get_queryset(self, entity):
            # TODO: test
            # TODO: filter deleted ?? what about current quote behaviour ??
            return Quote.objects.filter(relations__object_entity=entity.id,
                                        relations__type=constants.REL_SUB_LINKED_QUOTE,
                                       )


    class SalesOrdersBlock(_LinkedStuffBlock):
        id_                = QuerysetBlock.generate_id('opportunities', 'sales_orders')
        dependencies       = (Relation, SalesOrder)
        relation_type_deps = (constants.REL_OBJ_LINKED_SALESORDER, )
        verbose_name       = _(u"Salesorders linked to the opportunity")
        template_name      = 'opportunities/templatetags/block_sales_orders.html'

        _ct = _get_ct(SalesOrder)

        def _get_queryset(self, entity):
            # TODO: test
            return SalesOrder.objects.filter(is_deleted=False,
                                             relations__object_entity=entity.id,
                                             relations__type=constants.REL_SUB_LINKED_SALESORDER,
                                            )


    class InvoicesBlock(_LinkedStuffBlock):
        id_                = QuerysetBlock.generate_id('opportunities', 'invoices')
        dependencies       = (Relation, Invoice)
        relation_type_deps = (constants.REL_OBJ_LINKED_INVOICE, )
        verbose_name       = _(u"Invoices linked to the opportunity")
        template_name      = 'opportunities/templatetags/block_invoices.html'

        _ct = _get_ct(Invoice)

        def _get_queryset(self, entity):
            # TODO: test
            return Invoice.objects.filter(is_deleted=False,
                                          relations__object_entity=entity.id,
                                          relations__type=constants.REL_SUB_LINKED_INVOICE,
                                         )


    quotes_block      = QuotesBlock()
    salesorders_block = SalesOrdersBlock()
    invoices_block    = InvoicesBlock()

    blocks_list += (
        quotes_block,
        salesorders_block,
        invoices_block,
    )
