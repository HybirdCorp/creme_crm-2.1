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

from django.db.models import (CharField, BooleanField, TextField, DateTimeField,
        ForeignKey, PositiveIntegerField, PROTECT)
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _, ugettext
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

from creme.creme_core.models import CremeModel # CremeEntity
from creme.creme_core.models.fields import CremeUserForeignKey


class UserMessagePriority(CremeModel):
    title     = CharField(_(u'Title'), max_length=200)
    is_custom = BooleanField(default=True).set_tags(viewable=False) #used by creme_config

    class Meta:
        app_label = 'assistants'
        verbose_name = _(u'Priority of user message')
        verbose_name_plural = _(u'Priorities of user message')
        ordering = ('title',)

    def __unicode__(self):
        return self.title


class UserMessage(CremeModel):
    title         = CharField(_(u'Title'), max_length=200)
    body          = TextField(_(u'Message body'))
    creation_date = DateTimeField(_(u"Creation date"))
    priority      = ForeignKey(UserMessagePriority, verbose_name=_(u'Priority'), on_delete=PROTECT)
    sender        = CremeUserForeignKey(verbose_name=_(u'Sender'), related_name='sent_assistants_messages_set')
    recipient     = CremeUserForeignKey(verbose_name=_(u'Recipient'), related_name='received_assistants_messages_set') #, null=True

    email_sent = BooleanField(default=False)

    #TODO: use a True ForeignKey to CremeEntity (do not forget to remove the signal handlers)
    entity_content_type = ForeignKey(ContentType, null=True)
    entity_id           = PositiveIntegerField(null=True)
    creme_entity        = GenericForeignKey(ct_field="entity_content_type", fk_field="entity_id")

    class Meta:
        app_label = 'assistants'
        verbose_name = _(u'User message')
        verbose_name_plural = _(u'User messages')

    def __unicode__(self):
        return self.title

    @staticmethod
    def get_messages(entity, user):
        return UserMessage.objects.filter(entity_id=entity.id, recipient=user).select_related('sender')

    @staticmethod
    def get_messages_for_home(user):
        return UserMessage.objects.filter(recipient=user).select_related('sender')

    @staticmethod
    def get_messages_for_ctypes(ct_ids, user):
        return UserMessage.objects.filter(entity_content_type__in=ct_ids, recipient=user).select_related('sender')

    @staticmethod
    def create_messages(users, title, body, priority_id, sender, entity):
        """@param users A sequence of User objects. Team are treated as several Users. Duplicates are removed.
        """
        users_map = {}
        for user in users:
            if user.is_team:
                users_map.update(user.teammates)
            else:
                users_map[user.id] = user

        now_value = now()

        for user in users_map.itervalues():
            msg = UserMessage(title=title, body=body, creation_date=now_value,
                              priority_id=priority_id,
                              sender=sender, recipient=user, email_sent=False,
                             )
            msg.creme_entity = entity
            msg.save()

    @staticmethod
    def send_mails():
        from django.core.mail import EmailMessage, get_connection
        from django.conf import settings

        usermessages = list(UserMessage.objects.filter(email_sent=False))
        subject_format = ugettext(u'User message from Creme: %s')
        body_format    = ugettext(u'%(user)s send you the following message:\n%(body)s')
        EMAIL_SENDER   = settings.EMAIL_SENDER

        messages = [EmailMessage(subject_format % msg.title,
                                 body_format % {'user': msg.sender, 'body': msg.body},
                                 EMAIL_SENDER, [msg.recipient.email]
                                )
                        for msg in usermessages if msg.recipient.email
                   ]

#        try:
#            connection = get_connection()
#            connection.open()
#            connection.send_messages(messages)
#            connection.close()
#        except Exception, e: # wtf ??
#            raise e
        with get_connection() as connection:
            connection.send_messages(messages)

        for msg in usermessages:
            msg.email_sent = True
            msg.save()
