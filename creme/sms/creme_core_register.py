# -*- coding: utf-8 -*-

################################################################################
#    Creme is a free/open-source Customer Relationship Management software
#    Copyright (C) 2009-2010  Hybird
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
from creme_core.gui.menu import creme_menu
from creme_core.gui.block import block_registry

from sms.models import SMSCampaign, MessagingList
from sms.blocks import messaging_lists_block, recipients_block, contacts_block, messages_block, sendings_block


creme_registry.register_entity_models(SMSCampaign, MessagingList)
creme_registry.register_app('sms', _(u'SMS'), '/sms')

creme_menu.register_app('sms', '/sms/', "SMS")

reg_menu = creme_menu.register_menu
reg_menu('sms', '/sms/',                   _(u'Portal'))
reg_menu('sms', '/sms/campaigns' ,         _(u'All campaigns'))
reg_menu('sms', '/sms/campaign/add',       _(u'Add a campaign'))
reg_menu('sms', '/sms/messaging_lists',    _(u'All messaging lists'))
reg_menu('sms', '/sms/messaging_list/add', _(u'Add a messaging list'))
reg_menu('sms', '/sms/templates',          _(u'All message templates'))
reg_menu('sms', '/sms/template/add',       _(u'Add a message template'))

block_registry.register(messaging_lists_block, recipients_block, contacts_block, messages_block, sendings_block)
