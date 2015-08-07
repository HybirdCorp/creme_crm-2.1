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

from django.contrib.contenttypes.models import ContentType
from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.utils.translation import ugettext as _

from creme.creme_core.auth.decorators import login_required, permission_required
from creme.creme_core.models import ButtonMenuItem
from creme.creme_core.utils import get_from_POST_or_404
from creme.creme_core.views.generic import add_model_with_popup, inner_popup

from ..forms.button_menu import ButtonMenuAddForm, ButtonMenuEditForm


@login_required
@permission_required('creme_core.can_admin')
def add(request):
    return add_model_with_popup(request, ButtonMenuAddForm,
                                _(u'New buttons configuration'),
                                submit_label=_(u'Save the configuration'),
                               )

@login_required
#@permission_required('creme_config')
def portal(request):
    return render(request, 'creme_config/button_menu_portal.html')

@login_required
@permission_required('creme_core.can_admin')
def edit(request, ct_id):
    ct_id = int(ct_id) or None
    bmi = ButtonMenuItem.objects.filter(content_type=ct_id).order_by('order')

    if not bmi:
        raise Http404 #bof bof

    if request.method == 'POST':
        buttons_form = ButtonMenuEditForm(bmi, ct_id, user=request.user, data=request.POST)

        if buttons_form.is_valid():
            buttons_form.save()
    else:
        buttons_form = ButtonMenuEditForm(bmi, ct_id, user=request.user)

    title = _(u'Edit configuration for «%s»') % ContentType.objects.get_for_id(ct_id) \
            if ct_id else \
            _(u'Edit default configuration')

    return inner_popup(request,
                       'creme_core/generics/blockform/edit_popup.html',
                       {'form':  buttons_form,
                        'title': title,
                        'submit_label': _('Save the modifications'),
                       },
                       is_valid=buttons_form.is_valid(),
                       reload=False,
                       delegate_reload=True,
                      )

@login_required
@permission_required('creme_core.can_admin')
def delete(request):
    ct_id = get_from_POST_or_404(request.POST, 'id')
    ButtonMenuItem.objects.filter(content_type=ct_id).delete()

    return HttpResponse()
