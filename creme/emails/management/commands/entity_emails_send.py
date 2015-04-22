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

from django.core.management.base import BaseCommand

from creme.creme_core.models.lock import Mutex, MutexLockedException

from creme.emails import get_entityemail_model
from creme.emails.constants import MAIL_STATUS_NOTSENT, MAIL_STATUS_SENDINGERROR
#from creme.emails.models import EntityEmail

LOCK_NAME = "entity_emails_send"

#NB: python manage.py entity_emails_send

class Command(BaseCommand):
    help = "Send all unsent mails that have to be."

    def handle(self, *args, **options):
        try:
            lock = Mutex.get_n_lock(LOCK_NAME)
        except MutexLockedException:
            self.stderr.write('A process is already running')
        else:
#            for email in EntityEmail.objects.filter(status__in=[MAIL_STATUS_NOTSENT, MAIL_STATUS_SENDINGERROR]):
            for email in get_entityemail_model().objects.filter(status__in=[MAIL_STATUS_NOTSENT, MAIL_STATUS_SENDINGERROR]):
                email.send()

            Mutex.graceful_release(LOCK_NAME)
