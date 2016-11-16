# -*- coding: utf-8 -*-

################################################################################
#    Creme is a free/open-source Customer Relationship Management software
#    Copyright (C) 2009-2016  Hybird
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

from django.db.models import CharField, TextField, BooleanField
from django.utils.translation import ugettext_lazy as _

from creme.creme_core.models import CremeModel
from creme.creme_core.models.fields import BasicAutoField


class TaskStatus(CremeModel):
    name        = CharField(_('Name'), max_length=100)
    color_code  = CharField(_('Color'), max_length=100, blank=True)
    description = TextField(_('Description'))
    is_custom   = BooleanField(default=True).set_tags(viewable=False)  # Used by creme_config
    order       = BasicAutoField(_('Order'))  # Used by creme_config

    class Meta:
        app_label = 'projects'
        verbose_name = _(u'Status of task')
        verbose_name_plural = _(u'Statuses of task')
        ordering = ('order',)

    def __unicode__(self):
        return self.name
