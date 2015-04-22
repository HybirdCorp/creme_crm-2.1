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
from django.shortcuts import get_object_or_404, render

from django.utils.translation import ugettext_lazy as _, ugettext

from creme.creme_core.auth.decorators import login_required, permission_required
from creme.creme_core.utils import get_from_POST_or_404
from creme.creme_core.views.generic import (add_entity, add_to_entity,
        view_entity, edit_entity, list_view)

from ..forms.graph import GraphForm, AddRelationTypesForm
from ..models import Graph


@login_required
@permission_required(('graphs', 'graphs.add_graph'))
def add(request):
    return add_entity(request, GraphForm,
                      extra_template_dict={'submit_label': _('Save the graph')},
                     )

@login_required
@permission_required('graphs')
def dl_png(request, graph_id):
    graph = get_object_or_404(Graph, pk=graph_id)
    user  = request.user

    user.has_perm_to_view_or_die(graph)

    try:
        return graph.generate_png(user)
    except Graph.GraphException:
        return render(request, 'graphs/graph_error.html',
                      {'error_message': ugettext(u"This graph is too big!")},
                     )

@login_required
@permission_required('graphs')
def edit(request, graph_id):
    return edit_entity(request, graph_id, Graph, GraphForm)

@login_required
@permission_required('graphs')
def detailview(request, graph_id):
    return view_entity(request, graph_id, Graph, '/graphs/graph', 'graphs/view_graph.html')

@login_required
@permission_required('graphs')
def listview(request):
    return list_view(request, Graph, extra_dict={'add_url': '/graphs/graph/add'})

@login_required
@permission_required('graphs')
def add_relation_types(request, graph_id):
    return add_to_entity(request, graph_id, AddRelationTypesForm,
                         ugettext(u'Add relation types to <%s>'), entity_class=Graph,
                        )

@login_required
@permission_required('graphs')
def delete_relation_type(request, graph_id):
    rtypes_id = get_from_POST_or_404(request.POST, 'id')
    graph     = get_object_or_404(Graph, pk=graph_id)

    request.user.has_perm_to_change_or_die(graph)
    graph.orbital_relation_types.remove(rtypes_id)

    return HttpResponse("", content_type="text/javascript")
