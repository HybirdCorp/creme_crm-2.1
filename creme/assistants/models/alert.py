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

from collections import defaultdict

from django.db.models import (CharField, TextField, BooleanField, DateTimeField,
        ForeignKey, PositiveIntegerField)
from django.db.models.signals import pre_delete
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.generic import GenericForeignKey

from creme.creme_core.models import CremeModel, CremeEntity
from creme.creme_core.models.fields import CremeUserForeignKey
from creme.creme_core.core.function_field import (FunctionField, FunctionFieldResult,
        FunctionFieldResultsList)
from creme.creme_core.signals import pre_merge_related


class Alert(CremeModel):
    title               = CharField(max_length=200)
    description         = TextField(_(u'Description'), blank=True, null=True)
    is_validated        = BooleanField(_('Validated'), editable=False, default=False)
    reminded            = BooleanField(editable=False, default=False) #need by creme_core.core.reminder
    trigger_date        = DateTimeField(_(u"Trigger date"))

    entity_content_type = ForeignKey(ContentType, related_name="alert_entity_set", editable=False)
    entity_id           = PositiveIntegerField(editable=False)
    creme_entity        = GenericForeignKey(ct_field="entity_content_type", fk_field="entity_id")

    user                = CremeUserForeignKey(verbose_name=_('Owner user')) #verbose_name=_(u"Assigned to")

    class Meta:
        app_label = 'assistants'
        verbose_name = _('Alert')
        verbose_name_plural = _(u'Alerts')

    def __unicode__(self):
        return self.title

    def get_edit_absolute_url(self):
        return '/assistants/alert/edit/%s/' % self.id

    @staticmethod
    def get_alerts(entity):
        return Alert.objects.filter(is_validated=False, entity_id=entity.id).select_related('user')

    @staticmethod
    def get_alerts_for_home(user):
        return Alert.objects.filter(is_validated=False, user=user).select_related('user')

    @staticmethod
    def get_alerts_for_ctypes(ct_ids, user):
        return Alert.objects.filter(entity_content_type__in=ct_ids, user=user, is_validated=False).select_related('user')

    def get_related_entity(self): #for generic views
        return self.creme_entity


#TODO: can delete this with  a WeakForeignKey ??
def _dispose_entity_alerts(sender, instance, **kwargs):
    Alert.objects.filter(entity_id=instance.id).delete()

def _handle_merge(sender, other_entity, **kwargs):
    for alert in Alert.objects.filter(entity_id=other_entity.id):
        alert.creme_entity = sender
        alert.save()

pre_delete.connect(_dispose_entity_alerts, sender=CremeEntity)
pre_merge_related.connect(_handle_merge)


class _GetAlerts(FunctionField):
    name         = 'assistants-get_alerts'
    verbose_name = _(u"Alerts")

    def __call__(self, entity):
        cache = getattr(entity, '_alerts_cache', None)

        if cache is None:
            cache = entity._alerts_cache = list(Alert.objects
                                                     .filter(entity_id=entity.id, is_validated=False)
                                                     .order_by('trigger_date')
                                                     .values_list('title', flat=True)
                                               )

        return FunctionFieldResultsList(FunctionFieldResult(title) for title in cache)

    @classmethod
    def populate_entities(cls, entities):
        alerts_map = defaultdict(list)

        for title, e_id in Alert.objects.filter(entity_id__in=[e.id for e in entities], is_validated=False) \
                                        .order_by('trigger_date') \
                                        .values_list('title', 'entity_id'):
            alerts_map[e_id].append(title)

        for entity in entities:
            entity._alerts_cache = alerts_map[entity.id]


CremeEntity.function_fields.add(_GetAlerts())
