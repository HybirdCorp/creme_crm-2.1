# -*- coding: utf-8 -*-

################################################################################
#    Creme is a free/open-source Customer Relationship Management software
#    Copyright (C) 2012-2015  Hybird
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

from django.utils.translation import ugettext as _

from creme.creme_core.views.generic import app_portal

from creme.creme_config.utils import generate_portal_url

from .. import get_pollform_model, get_pollreply_model


def portal(request):
    PollForm  = get_pollform_model()
    PollReply = get_pollreply_model()
    stats = ((_('Number of forms'),   PollForm.objects.count()),
             (_('Number of replies'), PollReply.objects.count()),
            )

    return app_portal(request, 'polls', 'polls/portal.html', (PollForm, PollReply),
                      stats, config_url=generate_portal_url('polls')
                     )
