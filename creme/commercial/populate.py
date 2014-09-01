# -*- coding: utf-8 -*-

################################################################################
#    Creme is a free/open-source Customer Relationship Management software
#    Copyright (C) 2009-2014  Hybird
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

from django.utils.translation import ugettext as _
from django.conf import settings

from creme.creme_core.core.entity_cell import EntityCellRegularField
from creme.creme_core.models import (RelationType, CremePropertyType, SettingValue,
    BlockDetailviewLocation, SearchConfigItem, ButtonMenuItem, HeaderFilter)
from creme.creme_core.utils import create_if_needed
from creme.creme_core.blocks import relations_block, properties_block, customfields_block, history_block
from creme.creme_core.management.commands.creme_populate import BasePopulator

from creme.persons.models import Contact, Organisation

from .blocks import *
from .buttons import complete_goal_button
from .constants import *
from .models import *
from .setting_keys import notification_key, orga_approaches_key


logger = logging.getLogger(__name__)


class Populator(BasePopulator):
    dependencies = ['creme_core', 'persons']

    def populate(self):
        RelationType.create((REL_SUB_SOLD_BY,       _(u'has sold')),
                            (REL_OBJ_SOLD_BY,       _(u'has been sold by')))
        RelationType.create((REL_SUB_COMPLETE_GOAL, _(u'completes a goal of the commercial action')),
                            (REL_OBJ_COMPLETE_GOAL, _(u'is completed thanks to'),              [Act]))

        CremePropertyType.create(PROP_IS_A_SALESMAN, _(u'is a salesman'), [Contact])

        for i, title in enumerate([_('Phone calls'), _('Show'), _('Demo')], start=1):
            create_if_needed(ActType, {'pk': i}, title=title, is_custom=False)

        BlockDetailviewLocation.create(block_id=approaches_block.id_, order=10, zone=BlockDetailviewLocation.RIGHT)
        BlockDetailviewLocation.create(block_id=approaches_block.id_, order=10, zone=BlockDetailviewLocation.RIGHT, model=Contact)
        BlockDetailviewLocation.create(block_id=approaches_block.id_, order=10, zone=BlockDetailviewLocation.RIGHT, model=Organisation)

        BlockDetailviewLocation.create_4_model_block(order=5, zone=BlockDetailviewLocation.LEFT, model=Act)
        BlockDetailviewLocation.create(block_id=act_objectives_block.id_,        order=10,  zone=BlockDetailviewLocation.LEFT,  model=Act)
        BlockDetailviewLocation.create(block_id=related_opportunities_block.id_, order=20,  zone=BlockDetailviewLocation.LEFT,  model=Act)
        BlockDetailviewLocation.create(block_id=customfields_block.id_,          order=40,  zone=BlockDetailviewLocation.LEFT,  model=Act)
        BlockDetailviewLocation.create(block_id=properties_block.id_,            order=450, zone=BlockDetailviewLocation.LEFT,  model=Act)
        BlockDetailviewLocation.create(block_id=relations_block.id_,             order=500, zone=BlockDetailviewLocation.LEFT,  model=Act)
        BlockDetailviewLocation.create(block_id=history_block.id_,               order=20,  zone=BlockDetailviewLocation.RIGHT, model=Act)

        BlockDetailviewLocation.create(block_id=pattern_components_block.id_, order=10,  zone=BlockDetailviewLocation.TOP,   model=ActObjectivePattern)
        BlockDetailviewLocation.create_4_model_block(order=5, zone=BlockDetailviewLocation.LEFT, model=ActObjectivePattern)
        BlockDetailviewLocation.create(block_id=customfields_block.id_,       order=40,  zone=BlockDetailviewLocation.LEFT,  model=ActObjectivePattern)
        BlockDetailviewLocation.create(block_id=properties_block.id_,         order=450, zone=BlockDetailviewLocation.LEFT,  model=ActObjectivePattern)
        BlockDetailviewLocation.create(block_id=relations_block.id_,          order=500, zone=BlockDetailviewLocation.LEFT,  model=ActObjectivePattern)
        BlockDetailviewLocation.create(block_id=history_block.id_,            order=20,  zone=BlockDetailviewLocation.RIGHT, model=ActObjectivePattern)

        BlockDetailviewLocation.create(block_id=segment_descriptions_block.id_, order=10,  zone=BlockDetailviewLocation.TOP,   model=Strategy)
        BlockDetailviewLocation.create_4_model_block(order=5, zone=BlockDetailviewLocation.LEFT, model=Strategy)
        BlockDetailviewLocation.create(block_id=customfields_block.id_,         order=40,  zone=BlockDetailviewLocation.LEFT,  model=Strategy)
        BlockDetailviewLocation.create(block_id=evaluated_orgas_block.id_,      order=50,  zone=BlockDetailviewLocation.LEFT,  model=Strategy)
        BlockDetailviewLocation.create(block_id=assets_block.id_,               order=60,  zone=BlockDetailviewLocation.LEFT,  model=Strategy)
        BlockDetailviewLocation.create(block_id=charms_block.id_,               order=70,  zone=BlockDetailviewLocation.LEFT,  model=Strategy)
        BlockDetailviewLocation.create(block_id=properties_block.id_,           order=450, zone=BlockDetailviewLocation.LEFT,  model=Strategy)
        BlockDetailviewLocation.create(block_id=relations_block.id_,            order=500, zone=BlockDetailviewLocation.LEFT,  model=Strategy)
        BlockDetailviewLocation.create(block_id=history_block.id_,              order=20,  zone=BlockDetailviewLocation.RIGHT, model=Strategy)

        if 'creme.assistants' in settings.INSTALLED_APPS:
            logger.info('Assistants app is installed => we use the assistants blocks on detail views')

            from creme.assistants.blocks import alerts_block, memos_block, todos_block, messages_block

            for model in (Act, ActObjectivePattern, Strategy):
                BlockDetailviewLocation.create(block_id=todos_block.id_,    order=100, zone=BlockDetailviewLocation.RIGHT, model=model)
                BlockDetailviewLocation.create(block_id=memos_block.id_,    order=200, zone=BlockDetailviewLocation.RIGHT, model=model)
                BlockDetailviewLocation.create(block_id=alerts_block.id_,   order=300, zone=BlockDetailviewLocation.RIGHT, model=model)
                BlockDetailviewLocation.create(block_id=messages_block.id_, order=400, zone=BlockDetailviewLocation.RIGHT, model=model)


        create_hf = HeaderFilter.create
        create_hf(pk='commercial-hf_act', name=_(u"Com Action view"), model=Act,
                  cells_desc=[(EntityCellRegularField, {'name': 'name'}),
                              (EntityCellRegularField, {'name': 'expected_sales'}),
                              (EntityCellRegularField, {'name': 'due_date'}),
                             ],
                 )
        create_hf(pk='commercial-hf_strategy', name=_(u"Strategy view"), model=Strategy,
                  cells_desc=[(EntityCellRegularField, {'name': 'name'})],
                 )
        create_hf(pk='commercial-hf_objpattern', name=_(u"Objective pattern view"), model=ActObjectivePattern,
                  cells_desc=[(EntityCellRegularField, {'name': 'name'}),
                              (EntityCellRegularField, {'name': 'segment'}),
                             ]
                 )


        ButtonMenuItem.create_if_needed(pk='commercial-complete_goal_button', model=None, button=complete_goal_button, order=60)

        SearchConfigItem.create_if_needed(Act, ['name', 'expected_sales', 'cost', 'goal'])
        SearchConfigItem.create_if_needed(Strategy, ['name'])

        SettingValue.create_if_needed(key=notification_key,    user=None, value=True)
        SettingValue.create_if_needed(key=orga_approaches_key, user=None, value=True)
