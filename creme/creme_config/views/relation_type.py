# -*- coding: utf-8 -*-

################################################################################
#    Creme is a free/open-source Customer Relationship Management software
#    Copyright (C) 2009-2014  Hybird
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

from django.http import HttpResponse, Http404
from django.shortcuts import render, get_object_or_404
from django.utils.translation import ugettext as _

from creme.creme_core.auth.decorators import login_required, permission_required
from creme.creme_core.models import RelationType, SemiFixedRelationType
from creme.creme_core.views.generic import add_model_with_popup, inner_popup
from creme.creme_core.utils import get_from_POST_or_404

from ..forms.relation_type import RelationTypeCreateForm, RelationTypeEditForm, SemiFixedRelationTypeCreateForm


@login_required
@permission_required('creme_config')
def portal(request):
    return render(request, 'creme_config/relation_type_portal.html')

@login_required
@permission_required('creme_config.can_admin')
def add(request):
    return add_model_with_popup(request, RelationTypeCreateForm, _(u'New custom type'))

@login_required
@permission_required('creme_config.can_admin')
def add_semi_fixed(request):
    return add_model_with_popup(request, SemiFixedRelationTypeCreateForm, _(u'New semi-fixed type of relationship'))

@login_required
@permission_required('creme_config.can_admin')
def edit(request, relation_type_id):
    relation_type = get_object_or_404(RelationType, pk=relation_type_id)

    if not relation_type.is_custom: #TODO: in a generic method (can_edit or die() ?) and use edit_model_with_popup() ?
        raise Http404("Can't edit a standard RelationType")

    if request.method == 'POST':
        form = RelationTypeEditForm(relation_type, user=request.user, data=request.POST)

        if form.is_valid():
            form.save()
    else:
        form = RelationTypeEditForm(instance=relation_type, user=request.user)

    return inner_popup(request,
                       'creme_core/generics/blockform/edit_popup.html',
                       {'form':  form,
                        'title': _(u'Edit the type "%s"') % relation_type,
                       },
                       is_valid=form.is_valid(),
                       reload=False,
                       delegate_reload=True,
                      )

@login_required
@permission_required('creme_config.can_admin')
def delete(request):
    relation_type = get_object_or_404(RelationType, pk=get_from_POST_or_404(request.POST, 'id'))

    if not relation_type.is_custom:
        raise Http404("Can't delete a standard RelationType")

    relation_type.delete()

    return HttpResponse()

@login_required
@permission_required('creme_config.can_admin')
def delete_semi_fixed(request):
    semifixed_rtype = get_object_or_404(SemiFixedRelationType, pk=get_from_POST_or_404(request.POST, 'id'))
    semifixed_rtype.delete()

    return HttpResponse()
