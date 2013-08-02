# -*- coding: utf-8 -*-

################################################################################
#    Creme is a free/open-source Customer Relationship Management software
#    Copyright (C) 2009-2013  Hybird
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

from creme.creme_core.registry import creme_registry
from creme.creme_core.gui import creme_menu, button_registry, block_registry, icon_registry, import_form_registry

from .models import Opportunity
from .buttons import linked_opportunity_button
from .blocks import blocks_list, OpportunityBlock
from .forms.lv_import import get_csv_form_builder


creme_registry.register_app('opportunities', _(u'Opportunities'), '/opportunities')
creme_registry.register_entity_models(Opportunity)

reg_item = creme_menu.register_app('opportunities', '/opportunities/').register_item
reg_item('/opportunities/',                _(u'Portal of opportunities'), 'opportunities')
reg_item('/opportunities/opportunities',   _(u'All opportunities'),       'opportunities')
reg_item('/opportunities/opportunity/add', Opportunity.creation_label,    'opportunities.add_opportunity')

block_registry.register_4_model(Opportunity, OpportunityBlock())
button_registry.register(linked_opportunity_button)

block_registry.register(*blocks_list)

icon_registry.register(Opportunity, 'images/opportunity_%(size)s.png')

import_form_registry.register(Opportunity, get_csv_form_builder)
