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

from creme.creme_core.auth.decorators import login_required, permission_required
from creme.creme_core.views.generic import edit_entity, list_view, view_entity

from .. import get_template_base_model
from ..forms.templatebase import TemplateBaseEditForm
#from ..models import TemplateBase


TemplateBase = get_template_base_model()


@login_required
@permission_required('billing')
def edit(request, template_id):
    return edit_entity(request, template_id, TemplateBase, TemplateBaseEditForm)

@login_required
@permission_required('recurrents')
def detailview(request, template_id):
    user = request.user
    has_perm = user.has_perm
    isnt_staff = not user.is_staff

    return view_entity(request, template_id, TemplateBase, '/billing/template',
                       'billing/view_template.html',
                       {'can_download':       False,
                        'can_create_order':   has_perm('billing.add_salesorder') and isnt_staff,
                        'can_create_invoice': has_perm('billing.add_invoice') and isnt_staff,
                       }
                      )

@login_required
@permission_required('billing')
def listview(request):
    return list_view(request, TemplateBase, extra_dict={'add_url': '/recurrents/generator/add'})
