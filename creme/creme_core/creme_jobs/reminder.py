# -*- coding: utf-8 -*-

################################################################################
#    Creme is a free/open-source Customer Relationship Management software
#    Copyright (C) 2016-2019  Hybird
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

from datetime import datetime

from django.utils.translation import gettext_lazy as _, gettext

from ..core.reminder import reminder_registry
from .base import JobType


class _ReminderType(JobType):
    id           = JobType.generate_id('creme_core', 'reminder')
    verbose_name = _('Reminders')
    periodic     = JobType.PSEUDO_PERIODIC

    def _execute(self, job):
        for reminder in reminder_registry:
            reminder.execute(job)

    def get_description(self, job):
        return [gettext('Execute all reminders')]

    def next_wakeup(self, job, now_value):  # We have to implement it because it is a PSEUDO_PERIODIC JobType
        total_wakeup = None

        for reminder in reminder_registry:
            wakeup = reminder.next_wakeup(now_value)

            if isinstance(wakeup, datetime):
                total_wakeup = wakeup if total_wakeup is None else min(total_wakeup, wakeup)

        return total_wakeup


reminder_type = _ReminderType()
