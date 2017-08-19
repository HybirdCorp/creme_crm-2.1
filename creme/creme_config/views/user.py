# -*- coding: utf-8 -*-

################################################################################
#    Creme is a free/open-source Customer Relationship Management software
#    Copyright (C) 2009-2017  Hybird
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
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _

from creme.creme_core.auth.decorators import login_required, superuser_required
from creme.creme_core.core.exceptions import ConflictError
from creme.creme_core.views.decorators import POST_only
from creme.creme_core.views import generic

from ..forms import user as user_forms
from .portal import _config_portal


@login_required
@superuser_required
def change_password(request, user_id):
    return generic.edit_model_with_popup(request, {'pk': user_id}, get_user_model(),
                                         user_forms.UserChangePwForm, _(u'Change password for «%s»'),
                                        )


@login_required
@superuser_required
def add(request):
    return generic.add_model_with_popup(request, user_forms.UserAddForm,
                                # _(u'New user'),
                                # submit_label=_('Save the user'),
                               )


@login_required
@superuser_required
def add_team(request):
    return generic.add_model_with_popup(request, user_forms.TeamCreateForm, _(u'New team'),
                                        submit_label=_(u'Save the team'),
                                       )


@login_required
def portal(request):
    return _config_portal(request, 'creme_config/user_portal.html')


@login_required
@superuser_required
def edit(request, user_id):
    user_filter = {'pk':       user_id,
                   'is_team':  False,
                  }

    if not request.user.is_staff:
        user_filter['is_staff'] = False

    return generic.edit_model_with_popup(request, user_filter, get_user_model(), user_forms.UserEditForm)


@login_required
@superuser_required
def edit_team(request, user_id):
    return generic.edit_model_with_popup(request,
                                         {'pk':       user_id,
                                          'is_team':  True,
                                          'is_staff': False,
                                         },
                                         get_user_model(), user_forms.TeamEditForm,
                                        )


@login_required
@superuser_required
def delete(request, user_id):
    """Delete a User (who can be a Team). Objects linked to this User are
    linked to a new User.
    """
    user = request.user

    if int(user_id) == user.id:
        raise ConflictError(_(u"You can't delete the current user."))

    user_to_delete = get_object_or_404(get_user_model(), pk=user_id)

    if user_to_delete.is_staff and not user.is_staff:
        return HttpResponse(_(u"You can't delete a staff user."), status=400)

    try:
        return generic.add_model_with_popup(request, user_forms.UserAssignationForm,
                                            _(u'Delete «%s» and assign his files to user') % user_to_delete,
                                            initial={'user_to_delete': user_to_delete},
                                            submit_label=_(u'Delete the user'),
                                           )
    except Exception:
        return HttpResponse(_(u"You can't delete this user."), status=400)


@login_required
@superuser_required
@POST_only
def deactivate(request, user_id):
    user = request.user

    if int(user_id) == user.id:
        raise ConflictError(_(u"You can't deactivate the current user."))

    user_to_deactivate = get_object_or_404(get_user_model(), pk=user_id)

    if user_to_deactivate.is_staff and not user.is_staff:
        return HttpResponse(_(u"You can't deactivate a staff user."), status=400)

    if user_to_deactivate.is_active:
        user_to_deactivate.is_active = False
        user_to_deactivate.save()

    return HttpResponse()


@login_required
@superuser_required
@POST_only
def activate(request, user_id):
    user_to_activate = get_object_or_404(get_user_model(), pk=user_id)

    if user_to_activate.is_staff and not request.user.is_staff:
        return HttpResponse(_(u"You can't activate a staff user."), status=400)

    if not user_to_activate.is_active:
        user_to_activate.is_active = True
        user_to_activate.save()

    return HttpResponse()
