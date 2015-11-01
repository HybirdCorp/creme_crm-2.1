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

import logging

from django.db.models import Q
from django.http import Http404
from django.utils.encoding import smart_str

from creme.creme_core.auth.decorators import login_required
from creme.creme_core.gui.listview import ListViewState
from creme.creme_core.models import EntityFilter, EntityCredentials, HeaderFilter
from creme.creme_core.registry import export_backend_registry
from creme.creme_core.utils import get_ct_or_404
from creme.creme_core.utils.chunktools import iter_as_slices


logger = logging.getLogger(__name__)

#TODO: stream response ??
@login_required
def dl_listview(request, ct_id, doc_type, header_only=False):
    ct    = get_ct_or_404(ct_id)
    model = ct.model_class()
    user  = request.user

    user.has_perm_to_export_or_die(model)

    backend = export_backend_registry.get_backend(doc_type)
    if backend is None:
        raise Http404('Unknown extension')

    # TODO: is it possible that session doesn't content the state (eg: url linked and open directly) ????
    current_lvs = ListViewState.get_state(request, url=request.GET['list_url'])

    # TODO: factorise (with list_view()) ?? in a ListViewState's method ???
    hf = HeaderFilter.objects.get(pk=current_lvs.header_filter_id)
#    cells = hf.cells
    cells = hf.filtered_cells

    writer = backend()
    writerow = writer.writerow
    writerow([smart_str(cell.title) for cell in cells])  # doesn't accept generator expression... ;(

    if not header_only:
        current_lvs.handle_research(request, cells)
        current_lvs.set_sort(model, cells, current_lvs.sort_field, current_lvs.sort_order)

        entities = model.objects.filter(Q(is_deleted=False) | Q(is_deleted=None)) \
                                .distinct()
        efilter_id = current_lvs.entity_filter_id

        if efilter_id:
            efilter = EntityFilter.objects.get(pk=efilter_id)
            entities = efilter.filter(entities)

        if current_lvs.extra_q:
            entities = entities.filter(current_lvs.extra_q)

        entities = entities.filter(current_lvs.get_q_with_research(model, cells))
        entities = EntityCredentials.filter(user, entities)
        entities = current_lvs.sort_query(entities)

        for entities_slice in iter_as_slices(entities, 256):
            hf.populate_entities(entities_slice)  # Optimisation time !!!

            for entity in entities_slice:
                line = []

                for cell in cells:
                    try:
                        res = cell.render_csv(entity, user)
                    except Exception as e:
                        logger.debug('Exception in CSV export: %s', e)
                        res = ''

                    line.append(smart_str(res) if res else '')

                writerow(line)

    writer.save(ct.model)

    return writer.response

@login_required
def dl_listview_header(request, ct_id, doc_type):
    return dl_listview(request, ct_id, doc_type, header_only=True)
