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
from django.utils.translation import ugettext_lazy as _

from creme.creme_core.forms import CremeModelForm
# from creme.creme_core.forms.widgets import UnorderedMultipleChoiceWidget

from ..models import UserMessage


class UserMessageForm(CremeModelForm):
    users = ModelMultipleChoiceField(queryset=get_user_model().objects.filter(is_staff=False),
                                     label=_(u'Recipients'),
                                     # widget=UnorderedMultipleChoiceWidget,
                                     help_text=_(u'Each time a team is selected, a message is sent to each teammate '
                                                 u'(do not worry, there can not be any duplicate).'
                                                ),
                                    )

    class Meta:
        model = UserMessage
        fields = ('title', 'body', 'priority')

    def __init__(self, entity, *args, **kwargs):
        super(UserMessageForm, self).__init__(*args, **kwargs)
        self.entity = entity

        self.fields['priority'].empty_label = None  # TODO: generalise this behavior to all forms ???

    def save(self, *args, **kwargs):
        # NB: we do not call super() because we create several instances
        cdata = self.cleaned_data
        UserMessage.create_messages(cdata['users'], cdata['title'], cdata['body'],
                                    cdata['priority'].id, self.user, self.entity,
                                   )
