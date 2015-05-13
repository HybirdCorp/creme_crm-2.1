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

import logging

from django.apps import apps
from django.core.urlresolvers import reverse_lazy as reverse
from django.utils.translation import ugettext_lazy as _

from creme.creme_core.auth import build_creation_perm
from creme.creme_core.core.setting_key import setting_key_registry
from creme.creme_core.gui import (creme_menu, button_registry, block_registry,
        icon_registry, import_form_registry, smart_columns_registry)
from creme.creme_core.models import RelationType
from creme.creme_core.registry import creme_registry

from . import get_opportunity_model
from .blocks import blocks_list, OpportunityBlock
from .buttons import linked_opportunity_button
from .constants import REL_SUB_TARGETS
from .forms.lv_import import get_csv_form_builder
#from .models import Opportunity
from .setting_keys import quote_key


logger = logging.getLogger(__name__)
Opportunity = get_opportunity_model()

creme_registry.register_app('opportunities', _(u'Opportunities'), '/opportunities')
creme_registry.register_entity_models(Opportunity)

reg_item = creme_menu.register_app('opportunities', '/opportunities/').register_item
reg_item('/opportunities/',                _(u'Portal of opportunities'), 'opportunities')
#reg_item('/opportunities/opportunities',   _(u'All opportunities'),       'opportunities')
#reg_item('/opportunities/opportunity/add', Opportunity.creation_label,    'opportunities.add_opportunity')
reg_item(reverse('opportunities__list_opportunities'), _(u'All opportunities'),    'opportunities')
reg_item(reverse('opportunities__create_opportunity'), Opportunity.creation_label, build_creation_perm(Opportunity))

block_registry.register_4_model(Opportunity, OpportunityBlock())
button_registry.register(linked_opportunity_button)

block_registry.register(*blocks_list)

icon_registry.register(Opportunity, 'images/opportunity_%(size)s.png')

setting_key_registry.register(quote_key)

import_form_registry.register(Opportunity, get_csv_form_builder)

smart_columns_registry.register_model(Opportunity).register_field('name') \
                                                  .register_field('sales_phase') \
                                                  .register_relationtype(REL_SUB_TARGETS)


if apps.is_installed('creme.billing'):
    from .constants import REL_SUB_LINKED_SALESORDER, REL_SUB_LINKED_INVOICE, REL_SUB_LINKED_QUOTE

    from creme.billing import get_invoice_model, get_quote_model, get_sales_order_model
    from creme.billing.registry import relationtype_converter
#    from creme.billing.models import Quote, Invoice, SalesOrder

    get_rtype = RelationType.objects.get

    try:
        linked_salesorder = get_rtype(id=REL_SUB_LINKED_SALESORDER)
        linked_invoice    = get_rtype(id=REL_SUB_LINKED_INVOICE)
        linked_quote      = get_rtype(id=REL_SUB_LINKED_QUOTE)
    except RelationType.DoesNotExist as e:
        logger.info("A problem occured: %s\n"
                    "It can happen during unitests or during the 'populate' phase. Otherwise, has the database correctly been populated?", e
                   )
    else:
        Invoice    = get_invoice_model()
        Quote      = get_quote_model()
        SalesOrder = get_sales_order_model()

        register_rtype = relationtype_converter.register
        register_rtype(Quote,      linked_quote,      SalesOrder, linked_salesorder)
        register_rtype(Quote,      linked_quote,      Invoice,    linked_invoice)
        register_rtype(SalesOrder, linked_salesorder, Invoice,    linked_invoice)

    del get_rtype
