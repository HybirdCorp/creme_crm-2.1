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

from datetime import datetime, time

from django.forms import TypedChoiceField
from django.utils.timezone import now, localtime
from django.utils.translation import ugettext_lazy as _, ugettext

from creme.creme_core.forms import CremeModelWithUserForm, CremeDateTimeField
from creme.creme_core.utils.dates import make_aware_dt

from ..models import ToDo


class ToDoEditForm(CremeModelWithUserForm):
    deadline      = CremeDateTimeField(label=_(u'Deadline'), required=False)
    deadline_hour = TypedChoiceField(label=_(u'Deadline hour'), coerce=int,
                                     choices=[(i, '%ih' % i) for i in xrange(0, 24)],
                                     required=False, empty_value=None, initial=8,
                                     help_text=_(u'The hour is used only if you set the deadline date.'),
                                    )

    class Meta:
        model = ToDo

    def __init__(self, entity, *args, **kwargs):
        super(ToDoEditForm, self).__init__(*args, **kwargs)
        self.entity = entity

        deadline = self.instance.deadline
        if deadline:
            self.fields['deadline_hour'].initial = localtime(deadline).hour

    def clean(self):
        cdata = self.cleaned_data

        if not self._errors:
            get_data = cdata.get
            deadline = get_data('deadline')

            if deadline:
                deadline_hour = get_data('deadline_hour') 

                if deadline_hour is None:
                    self._errors['deadline_hour'] = self.error_class(
                            [ugettext(u'The hour is required if you set a date.')]
                        )
                else:
                    cdata['deadline'] = make_aware_dt(datetime.combine(deadline,
                                                                       time(deadline_hour)
                                                                      )
                                                     )

        return cdata

    def save(self, *args, **kwargs):
        self.instance.creme_entity = self.entity
        return super(ToDoEditForm, self).save(*args, **kwargs)


class ToDoCreateForm(ToDoEditForm):
    def save(self, *args, **kwargs):
        self.instance.creation_date = now()
        return super(ToDoCreateForm, self).save(*args, **kwargs)
