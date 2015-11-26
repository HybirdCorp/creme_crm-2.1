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
#from django.conf import settings
from django.utils.translation import ugettext as _

from creme.creme_core.core.entity_cell import EntityCellRegularField
from creme.creme_core.models import SearchConfigItem, HeaderFilter, BlockDetailviewLocation
from creme.creme_core.blocks import properties_block, relations_block, customfields_block, history_block
from creme.creme_core.management.commands.creme_populate import BasePopulator

#from .models import Graph
from . import get_graph_model
from .blocks import root_nodes_block, orbital_rtypes_block
from .constants import DEFAULT_HFILTER_GRAPH


logger = logging.getLogger(__name__)


class Populator(BasePopulator):
    dependencies = ['creme_core']

    def populate(self):
        Graph = get_graph_model()

        HeaderFilter.create(pk=DEFAULT_HFILTER_GRAPH, name=_(u'Graph view'), model=Graph,
                            cells_desc=[(EntityCellRegularField, {'name': 'name'})],
                           )


        SearchConfigItem.create_if_needed(Graph, ['name'])


        if not BlockDetailviewLocation.config_exists(Graph):  # NB: no straightforward way to test that this populate script has not been already runned
            BlockDetailviewLocation.create_4_model_block(order=5, zone=BlockDetailviewLocation.LEFT, model=Graph)
            BlockDetailviewLocation.create(block_id=customfields_block.id_,   order=40,  zone=BlockDetailviewLocation.LEFT,  model=Graph)
            BlockDetailviewLocation.create(block_id=root_nodes_block.id_,     order=60,  zone=BlockDetailviewLocation.LEFT,  model=Graph)
            BlockDetailviewLocation.create(block_id=orbital_rtypes_block.id_, order=65,  zone=BlockDetailviewLocation.LEFT,  model=Graph)
            BlockDetailviewLocation.create(block_id=properties_block.id_,     order=450, zone=BlockDetailviewLocation.LEFT,  model=Graph)
            BlockDetailviewLocation.create(block_id=relations_block.id_,      order=500, zone=BlockDetailviewLocation.LEFT,  model=Graph)
            BlockDetailviewLocation.create(block_id=history_block.id_,        order=20,  zone=BlockDetailviewLocation.RIGHT, model=Graph)

            if apps.is_installed('creme.assistants'):
                logger.info('Assistants app is installed => we use the assistants blocks on detail view')

                from creme.assistants.blocks import alerts_block, memos_block, todos_block, messages_block

                BlockDetailviewLocation.create(block_id=todos_block.id_,    order=100, zone=BlockDetailviewLocation.RIGHT, model=Graph)
                BlockDetailviewLocation.create(block_id=memos_block.id_,    order=200, zone=BlockDetailviewLocation.RIGHT, model=Graph)
                BlockDetailviewLocation.create(block_id=alerts_block.id_,   order=300, zone=BlockDetailviewLocation.RIGHT, model=Graph)
                BlockDetailviewLocation.create(block_id=messages_block.id_, order=400, zone=BlockDetailviewLocation.RIGHT, model=Graph)
