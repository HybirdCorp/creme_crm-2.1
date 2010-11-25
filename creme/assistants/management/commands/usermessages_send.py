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

from django.core.management.base import BaseCommand
from django.utils import translation
from django.conf import settings

from creme_core.models import Lock

from assistants.models import UserMessage


LOCK_NAME = "sending_usermessages"

#NB: python manage.py usermessages_send

class Command(BaseCommand):
    help = "Send all unsended mails related to user messages that have to be."

    def handle(self, *args, **options):
        lock = Lock.objects.filter(name=LOCK_NAME)

        if not lock:
            try:
                lock = Lock(name=LOCK_NAME)
                lock.save()

                translation.activate(settings.LANGUAGE_CODE)
                UserMessage.send_mails()
            finally:
                lock.delete()
        else:
            print 'A process is already running'
