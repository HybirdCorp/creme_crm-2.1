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

import logging

from django.db.models import CharField, BooleanField, TextField, DateTimeField, PositiveIntegerField, ForeignKey
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.generic import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from creme_core.models import CremeModel


class CommercialApproach(CremeModel):
    title               = CharField(_(u'Title'), max_length=200)
    ok_or_in_futur      = BooleanField(_("Done ?"), editable=False)
    description         = TextField(_(u'Description'), blank=True, null=True)
    creation_date       = DateTimeField(_(u'Creation date'), blank=False, null=False)

    related_activity_id = PositiveIntegerField(null=True)

    entity_content_type = ForeignKey(ContentType, related_name="comapp_entity_set")
    entity_id           = PositiveIntegerField()

    creme_entity        = GenericForeignKey(ct_field="entity_content_type", fk_field="entity_id")

    class Meta:
        app_label = 'commercial'
        verbose_name = _(u'Commercial approach')
        verbose_name_plural = _(u'Commercial approaches')

    def get_related_activity(self):
        from activities.models import Activity
        try:
            return Activity.objects.get(pk=self.related_activity_id)
        except Activity.DoesNotExist:
            return None

    @staticmethod
    def get_approaches(entity_pk=None):
        if entity_pk:
            return CommercialApproach.objects.filter(entity_id=entity_pk, ok_or_in_futur=False)

        return CommercialApproach.objects.filter(ok_or_in_futur=False)
