# -*- coding: utf-8 -*-

################################################################################
#    Creme is a free/open-source Customer Relationship Management software
#    Copyright (C) 2009-2018  Hybird
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

from django.db.models import CharField
from django.utils.translation import ugettext_lazy as _

from .base import CremeModel


class Language(CremeModel):
    name = CharField(_(u'Name'), max_length=100)
    code = CharField(_(u'Code'), max_length=5)

    def __str__(self):
        return u'{} - {}'.format(self.name, self.code)

    class Meta:
        app_label = 'creme_core'
        verbose_name = _(u'Language')
        verbose_name_plural = _(u'Languages')
        ordering = ('name',)
