# -*- coding: utf-8 -*-

################################################################################
#    Creme is a free/open-source Customer Relationship Management software
#    Copyright (C) 2009-2010  Hybird
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

from django.http import HttpResponseRedirect, HttpResponse
from django.template.context import RequestContext
from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import get_object_or_404, render_to_response
from django.conf import settings

from creme_core.views.generic import add_model_with_popup, edit_model_with_popup
from creme_core.models import SearchConfigItem, SearchField
from creme_core.utils import get_from_POST_or_404

from creme_config.forms.search import SearchEditForm, SearchAddForm


@login_required
@permission_required('creme_config.can_admin')
def add(request):
    return add_model_with_popup(request, SearchAddForm, _(u'New search configuration'))

@login_required
@permission_required('creme_config')
def portal(request):
    return render_to_response('creme_config/search_portal.html',
                              {'SHOW_HELP': settings.SHOW_HELP},#TODO:Context processor ?
                              context_instance=RequestContext(request))

@login_required
@permission_required('creme_config.can_admin')
def edit(request, search_config_id):
    return edit_model_with_popup(request, {'pk': search_config_id}, SearchConfigItem, SearchEditForm)

@login_required
@permission_required('creme_config.can_admin')
def delete(request):
    search_cfg_id = get_from_POST_or_404(request.POST, 'id')

    SearchConfigItem.objects.filter(id=search_cfg_id).delete()
    SearchField.objects.filter(search_config_item=search_cfg_id).delete()

    return HttpResponse()
