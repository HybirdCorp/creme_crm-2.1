# -*- coding: utf-8 -*-

################################################################################
#    Creme is a free/open-source Customer Relationship Management software
#    Copyright (C) 2009-2017  Hybird
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

from django.core.urlresolvers import reverse
from django.db.models import (CharField, BooleanField, TextField, DateTimeField,
        ForeignKey, PositiveIntegerField)
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

from creme.creme_core.models import CremeModel  # CremeEntity
from creme.creme_core.models.fields import CremeUserForeignKey, CreationDateTimeField


class Action(CremeModel):
    title               = CharField(_(u'Title'), max_length=200)
    is_ok               = BooleanField(_(u'Expected reaction has been done'), editable=False, default=False)
    description         = TextField(_(u'Source action'), blank=True)
    creation_date       = CreationDateTimeField(_(u'Creation date'), editable=False)
    expected_reaction   = TextField(_(u'Target action'), blank=True)
    deadline            = DateTimeField(_(u'Deadline'))
    validation_date     = DateTimeField(_(u'Validation date'), blank=True, null=True, editable=False)

    # TODO: use a True ForeignKey to CremeEntity (do not forget to remove the signal handlers)
    entity_content_type = ForeignKey(ContentType, related_name="action_entity_set", editable=False)
    entity_id           = PositiveIntegerField(editable=False).set_tags(viewable=False)
    creme_entity        = GenericForeignKey(ct_field="entity_content_type", fk_field="entity_id")

    user                = CremeUserForeignKey(verbose_name=_(u'Owner user')) #verbose_name=_(u"Assigned to")

    class Meta:
        app_label = 'assistants'
        verbose_name = _(u'Action')
        verbose_name_plural = _(u'Actions')

    # def __init__ (self, *args , **kwargs):
    #     super(Action, self).__init__(*args, **kwargs)
    #
    #     if self.pk is None:
    #         self.is_ok = False

    def __unicode__(self):
        return self.title

    def get_edit_absolute_url(self):
        # return '/assistants/action/edit/%s/' % self.id
        return reverse('assistants__edit_action', args=(self.id,))

    @staticmethod
    def get_actions_it(entity, today):
        return Action.objects.filter(entity_id=entity.id, is_ok=False, deadline__gt=today) \
                             .select_related('user')

    @staticmethod
    def get_actions_nit(entity, today):
        return Action.objects.filter(entity_id=entity.id, is_ok=False, deadline__lte=today) \
                             .select_related('user')

    @staticmethod
    def get_actions_it_for_home(user, today):
        # return Action.objects.filter(is_ok=False, deadline__gt=today, user=user) \
        return Action.objects.filter(is_ok=False, deadline__gt=today, user__in=[user] + user.teams) \
                             .select_related('user')

    @staticmethod
    def get_actions_nit_for_home(user, today):
        # return Action.objects.filter(is_ok=False, deadline__lte=today, user=user) \
        return Action.objects.filter(is_ok=False, deadline__lte=today, user__in=[user] + user.teams) \
                             .select_related('user')

    @staticmethod
    def get_actions_it_for_ctypes(ct_ids, user, today):
        # return Action.objects.filter(entity_content_type__in=ct_ids, user=user, is_ok=False, deadline__gt=today) \
        return Action.objects.filter(entity_content_type__in=ct_ids,
                                     user__in=[user] + user.teams,
                                     is_ok=False,
                                     deadline__gt=today,
                                    ) \
                             .select_related('user')

    @staticmethod
    def get_actions_nit_for_ctypes(ct_ids, user, today):
        # return Action.objects.filter(entity_content_type__in=ct_ids, user=user, is_ok=False, deadline__lte=today) \
        return Action.objects.filter(entity_content_type__in=ct_ids,
                                     user__in=[user] + user.teams,
                                     is_ok=False,
                                     deadline__lte=today
                                    ) \
                             .select_related('user')

    def get_related_entity(self):  # For generic views
        return self.creme_entity
