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

import logging

from django.core.mail import EmailMessage, get_connection
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.utils.timezone import now

from ..models import DateReminder


logger = logging.getLogger(__name__)
FIRST_REMINDER = 1


class Reminder(object):
    id_    = None   #overload with an unicode object ; use generate_id()
    model_ = None   #overload with a CremeModel

    def __init__(self):
        pass

    @staticmethod
    def generate_id(app_name, name):
        return u'reminder_%s-%s' % (app_name, name)

    def get_emails(self, object):
        return [getattr(settings, 'DEFAULT_USER_EMAIL', None)]

    def generate_email_subject (self, object):
        pass

    def generate_email_body(self, object):
        pass

    def get_Q_filter(self): #TODO: get_queryset instead ????
        pass

    def ok_for_continue (self):
        return True

    def send_mails(self, object):
        body    = self.generate_email_body(object)
        subject = self.generate_email_subject(object)

        EMAIL_SENDER = settings.EMAIL_SENDER
        messages = [EmailMessage(subject, body, EMAIL_SENDER, [email]) for email in self.get_emails(object)]

        try:
            connection = get_connection()
            connection.open()
            connection.send_messages(messages)
            connection.close()
        except Exception:
            logger.exception('Reminder.send_mails() failed')

    def execute(self):
        if not self.ok_for_continue():
            return

        model_ = self.__class__.model_ #TODO: why not self.model_ ???
        objects = model_.objects.filter(self.get_Q_filter())
        object_ct = ContentType.objects.get_for_model(model_)
        dt_now = now().replace(microsecond=0, second=0)
        reminder_filter = DateReminder.objects.filter

        for object in objects:
            #reminders = DateReminder.objects.filter(model_id=object.id, model_content_type=object_ct)
            #reminders = reminder_filter(model_id=object.id, model_content_type=object_ct)[:1]
            #if not reminders:
            if not reminder_filter(model_id=object.id, model_content_type=object_ct).exists():
                self.send_mails(object)
                date_reminder = DateReminder()
                date_reminder.date_of_remind = dt_now #factorise ??
                date_reminder.ident = FIRST_REMINDER
                date_reminder.object_of_reminder = object
                date_reminder.save()


class ReminderRegistry(object):
    def __init__(self):
        self._reminders = {}

    def register(self, reminder):
        """
        @type reminder creme_core.core.reminder.Reminder
        """
        reminders = self._reminders
        reminder_id = reminder.id_

        if reminders.has_key(reminder_id):
            logger.warning("Duplicate reminder's id or reminder registered twice : %s", reminder_id) #exception instead ???

        reminders[reminder_id] = reminder

    def __iter__(self):
        return self._reminders.iteritems()

    def itervalues(self):
        return self._reminders.itervalues()


reminder_registry = ReminderRegistry()
