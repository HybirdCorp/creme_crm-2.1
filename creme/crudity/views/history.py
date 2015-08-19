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
from django.shortcuts import render # render_to_response
#from django.template.context import RequestContext

from creme.creme_core.auth.decorators import login_required, permission_required
from creme.creme_core.utils import get_ct_or_404, jsonify
from creme.creme_core.views.blocks import build_context

from ..blocks import HistoryBlock
from ..registry import crudity_registry


@login_required
@permission_required('crudity')
def history(request):
#    blocks  = []
#    context = RequestContext(request)
#    get_ct  = ContentType.objects.get_for_model
#
#    for backend in crudity_registry.get_backends():
#        bmodel = backend.model
#        if bmodel:
#            blocks.append(HistoryBlock(get_ct(bmodel)).detailview_display(context))
#
#    return render_to_response("crudity/history.html", {'blocks': blocks}, context_instance=context)
    get_ct  = ContentType.objects.get_for_model
    blocks  = [HistoryBlock(get_ct(backend.model))
                   for backend in crudity_registry.get_backends()
                       if backend.model
              ]

    return render(request, 'crudity/history.html', {'blocks': blocks})

@jsonify
@login_required
@permission_required('crudity')
def reload(request, ct_id):
    block = HistoryBlock(get_ct_or_404(ct_id))
#    return [(block.id_, block.detailview_display(RequestContext(request)))]
    return [(block.id_, block.detailview_display(build_context(request)))]
