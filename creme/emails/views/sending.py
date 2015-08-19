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

from django.shortcuts import render, get_object_or_404
#from django.template import RequestContext
from django.utils.translation import ugettext as _

from creme.creme_core.auth.decorators import login_required, permission_required
from creme.creme_core.views.blocks import build_context
from creme.creme_core.views.generic import add_to_entity
from creme.creme_core.utils import jsonify

from .. import get_emailcampaign_model
from ..blocks import mails_block
from ..forms.sending import SendingCreateForm
from ..models import EmailSending #EmailCampaign


@login_required
@permission_required('emails')
def add(request, campaign_id):
    return add_to_entity(request, campaign_id, SendingCreateForm,
                         _(u'New sending for «%s»'),
#                         entity_class=EmailCampaign,
                         entity_class=get_emailcampaign_model(),
                         submit_label=_('Save the sending'),
                        )

def _get_sending(request, sending_id):
    sending  = get_object_or_404(EmailSending, pk=sending_id)
    campaign = sending.campaign

    request.user.has_perm_to_view_or_die(campaign)

    return sending

@login_required
@permission_required('emails')
def detailview(request, sending_id):
    return render(request, 'emails/popup_sending.html',
                  {'object': _get_sending(request, sending_id)},
                 )

#Useful method because EmailSending is not a CremeEntity (should be ?)
@jsonify
@login_required
@permission_required('emails')
def reload_block_mails(request, sending_id):
    #context = RequestContext(request)
    context = build_context(request)
    context['object'] = _get_sending(request, sending_id)

    return [(mails_block.id_, mails_block.detailview_display(context))]
