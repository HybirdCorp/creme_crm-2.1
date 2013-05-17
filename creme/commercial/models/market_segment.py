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

from django.db.models import CharField, ForeignKey
from django.utils.translation import ugettext_lazy as _, ugettext

from creme.creme_core.models import CremeModel, CremePropertyType


class MarketSegment(CremeModel):
    name          = CharField(_(u"Name"), max_length=100)
    property_type = ForeignKey(CremePropertyType, editable=False).set_tags(viewable=False)

    class Meta:
        app_label = "commercial"
        verbose_name = _(u'Market segment')
        verbose_name_plural = _(u'Market segments')

    def __unicode__(self):
        return self.name

    @staticmethod
    def generate_property_text(segment_name):
        return ugettext(u'is in the segment "%s"') % segment_name
