# -*- coding: utf-8 -*-

################################################################################
#    Creme is a free/open-source Customer Relationship Management software
#    Copyright (C) 2015  Hybird
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

from creme.creme_core.apps import CremeAppConfig


class MobileConfig(CremeAppConfig):
    name = 'creme.mobile'
    verbose_name = _(u'Mobile')
    dependencies = ['creme.persons', 'creme.activities']

    def register_creme_app(self, creme_registry):
        # NB: mandatory to get our own URLs
        creme_registry.register_app('mobile', _(u'Mobile'),
                                    credentials=creme_registry.CRED_NONE,
                                   )

    def register_blocks(self, block_registry):
        from .blocks import favorite_persons_block

        block_registry.register(favorite_persons_block)
