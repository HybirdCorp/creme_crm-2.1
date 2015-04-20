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

from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import ugettext_lazy as _, ugettext

from creme.creme_core.auth.decorators import login_required, permission_required
from creme.creme_core.utils import get_from_POST_or_404
from creme.creme_core.views.generic import (add_entity, add_to_entity,
        edit_entity, view_entity, list_view)

from ..models import MailingList
from ..forms.mailing_list import (MailingListForm, AddChildForm,
                                  AddContactsForm, AddOrganisationsForm,
                                  AddContactsFromFilterForm, AddOrganisationsFromFilterForm)


@login_required
@permission_required('emails')
@permission_required('emails.add_mailinglist')
def add(request):
    return add_entity(request, MailingListForm,
                      extra_template_dict={'submit_label': _('Save the mailing list')},
                     )

@login_required
@permission_required('emails')
def edit(request, ml_id):
    return edit_entity(request, ml_id, MailingList, MailingListForm)

@login_required
@permission_required('emails')
def detailview(request, ml_id):
    return view_entity(request, ml_id, MailingList, '/emails/mailing_list',
                       'emails/view_mailing_list.html',
                      )

@login_required
@permission_required('emails')
def listview(request):
    return list_view(request, MailingList, extra_dict={'add_url': '/emails/mailing_list/add'})

@login_required
@permission_required('emails')
def add_contacts(request, ml_id):
    return add_to_entity(request, ml_id, AddContactsForm,
                         ugettext('New contacts for <%s>'), entity_class=MailingList,
                        )

@login_required
@permission_required('emails')
def add_contacts_from_filter(request, ml_id):
    return add_to_entity(request, ml_id, AddContactsFromFilterForm,
                         ugettext('New contacts for <%s>'), entity_class=MailingList,
                        )

@login_required
@permission_required('emails')
def add_organisations(request, ml_id):
    return add_to_entity(request, ml_id, AddOrganisationsForm,
                         ugettext('New organisations for <%s>'), entity_class=MailingList,
                        )

@login_required
@permission_required('emails')
def add_organisations_from_filter(request, ml_id):
    return add_to_entity(request, ml_id, AddOrganisationsFromFilterForm,
                         ugettext('New organisations for <%s>'), entity_class=MailingList,
                        )

@login_required
@permission_required('emails')
def add_children(request, ml_id):
    return add_to_entity(request, ml_id, AddChildForm,
                         ugettext('New child lists for <%s>'), entity_class=MailingList,
                        )

@login_required
@permission_required('emails')
def _delete_aux(request, ml_id, deletor):
    subobject_id = get_from_POST_or_404(request.POST, 'id')
    ml = get_object_or_404(MailingList, pk=ml_id)

    request.user.has_perm_to_change_or_die(ml)

    deletor(ml, subobject_id)

    if request.is_ajax():
        return HttpResponse("", content_type="text/javascript")

    return redirect(ml)

def delete_contact(request, ml_id):
    return _delete_aux(request, ml_id, lambda ml, contact_id: ml.contacts.remove(contact_id))

def delete_organisation(request, ml_id):
    return _delete_aux(request, ml_id, lambda ml, orga_id: ml.organisations.remove(orga_id))

def delete_child(request, ml_id):
    return _delete_aux(request, ml_id, lambda ml, child_id: ml.children.remove(child_id))
