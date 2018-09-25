# -*- coding: utf-8 -*-

################################################################################
#    Creme is a free/open-source Customer Relationship Management software
#    Copyright (C) 2009-2018  Hybird
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
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _

from creme.creme_core.auth.decorators import login_required, permission_required
from creme.creme_core.utils import get_from_POST_or_404
from creme.creme_core.views import generic

from .. import get_graph_model
from ..forms import root_node as forms
from ..models import RootNode


# @login_required
# @permission_required('graphs')
# def add(request, graph_id):
#     return generic.add_to_entity(
#         request, graph_id, forms.AddRootNodesForm,
#         _('Add root nodes to «%s»'),
#         entity_class=get_graph_model(),
#         template='creme_core/generics/blockform/link_popup.html',
#     )
class RootNodesAdding(generic.add.AddingToEntity):
    # model = CremeEntity
    form_class = forms.AddRootNodesForm
    template_name = 'creme_core/generics/blockform/link_popup.html'
    title_format = _('Add root nodes to «{}»')
    entity_id_url_kwarg = 'graph_id'
    entity_classes = get_graph_model()
    # submit_label = _('Add') ??


@login_required
@permission_required('graphs')
def edit(request, root_id):
    return generic.edit_related_to_entity(
        request, root_id, RootNode, forms.EditRootNodeForm,
        _('Edit root node for «%s»'),
    )


@login_required
@permission_required('graphs')
def delete(request):
    root_node = get_object_or_404(RootNode, pk=get_from_POST_or_404(request.POST, 'id'))

    request.user.has_perm_to_change_or_die(root_node.graph)
    root_node.delete()

    return HttpResponse()
