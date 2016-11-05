# -*- coding: utf-8 -*-

################################################################################
#    Creme is a free/open-source Customer Relationship Management software
#    Copyright (C) 2009-2016  Hybird
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

from django.contrib.auth import get_user_model
from django.forms import ModelMultipleChoiceField
from django.utils.translation import ugettext as _

# from creme.creme_core.forms.widgets import UnorderedMultipleChoiceWidget

from creme.activities.forms.activity import ActivityCreateForm, CalendarActivityCreateForm

from .constants import PRIO_NOT_IMP_PK
from .models import UserMessage


def add_users_field(form):
    if isinstance(form, CalendarActivityCreateForm):
        return

    form.fields['informed_users'] = ModelMultipleChoiceField(queryset=get_user_model().objects.filter(is_staff=False),
                                                             # widget=UnorderedMultipleChoiceWidget,
                                                             required=False,
                                                             label=_(u'Users to keep informed'),
                                                            )

    form.blocks = form.blocks.new(('informed_users', 'Users to keep informed', ['informed_users']))


def save_users_field(form):
    if isinstance(form, CalendarActivityCreateForm):
        return

    cdata     = form.cleaned_data
    raw_users = cdata['informed_users']

    if not raw_users:
        return

    activity = form.instance
    title    = _(u'[Creme] Activity created: %s') % activity
    body     = _(u"""A new activity has been created: %(activity)s.
    Description: %(description)s.
    Start: %(start)s.
    End: %(end)s.
    Subjects: %(subjects)s.
    Participants: %(participants)s.""") % {
            'activity':     activity,
            'description':  activity.description,
            'start':        activity.start or _('not specified'),
            'end':          activity.end or _('not specified'),
            'subjects':     u' / '.join(unicode(e) for e in cdata['subjects']),
            'participants': u' / '.join(unicode(c) for c in form.participants),
        }

    # TODO: sender = the real user that created the activity ???
    UserMessage.create_messages(raw_users, title, body, PRIO_NOT_IMP_PK, activity.user, activity)


ActivityCreateForm.add_post_init_callback(add_users_field)
ActivityCreateForm.add_post_save_callback(save_users_field)
