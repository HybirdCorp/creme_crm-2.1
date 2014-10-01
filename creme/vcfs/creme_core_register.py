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

from django.utils.translation import ugettext_lazy as _

from creme.creme_core.gui.menu import creme_menu
from creme.creme_core.gui.button_menu import button_registry
from creme.creme_core.registry import creme_registry

from .buttons import generate_vcf_button


creme_registry.register_app('vcfs', _(u'Vcfs'), credentials=creme_registry.CRED_NONE)

creme_menu.get_app_item('persons').register_item('/vcfs/vcf', _(u'Import contact from VCF file'), 'persons.add_contact')

button_registry.register(generate_vcf_button)
