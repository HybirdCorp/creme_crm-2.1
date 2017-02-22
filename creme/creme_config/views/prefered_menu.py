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

from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.utils.translation import ugettext as _

from creme.creme_core.auth.decorators import login_required, permission_required
from creme.creme_core.views.generic import inner_popup

from ..forms.prefered_menu import PreferedMenuForm


@login_required
@permission_required('creme_core.can_admin')
def edit(request):
    if request.method == 'POST':
        form = PreferedMenuForm(user2edit=None, user=request.user, data=request.POST)

        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/creme_config/')
    else:
        form = PreferedMenuForm(user2edit=None, user=request.user)

    return render(request, 'creme_core/generics/blockform/edit.html',
                  {'form': form,
                   'title': _(u'Edit the default preferred menu'),
                  }
                 )


# TODO: improve generic.add_model_with_popup ????
@login_required  # No special permission needed
def edit_mine(request):
    user = request.user

    if request.method == 'POST':
        form = PreferedMenuForm(user2edit=user, user=user, data=request.POST)

        if form.is_valid():
            form.save()
    else:
        form = PreferedMenuForm(user2edit=user, user=user)

    return inner_popup(request, 'creme_core/generics/blockform/edit_popup.html',
                       {'form':  form,
                        'title': _(u'Edit my preferred menus'),
                        'submit_label': _('Save the modifications'),
                       },
                       is_valid=form.is_valid(),
                       reload=False,
                       delegate_reload=True,
                      )
