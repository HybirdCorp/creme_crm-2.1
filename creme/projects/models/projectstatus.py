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

from django.db.models import CharField, TextField
from django.utils.translation import ugettext_lazy as _, pgettext_lazy

from creme.creme_core.models import CremeModel
from creme.creme_core.models.fields import BasicAutoField, ColorField


class ProjectStatus(CremeModel):
    name        = CharField(_('Name'), max_length=100)
    # color_code  = CharField(_('Color'), max_length=100, blank=True)
    color_code  = ColorField(_('Color'), blank=True)
    description = TextField(_('Description'))
    order       = BasicAutoField(_('Order'))  # Used by creme_config

    def __unicode__(self):
        return self.name

    class Meta:
        app_label = 'projects'
        verbose_name = pgettext_lazy('projects-singular', u'Status of project')
        verbose_name_plural = pgettext_lazy('projects-plural', u'Status of project')
        ordering = ('order',)
