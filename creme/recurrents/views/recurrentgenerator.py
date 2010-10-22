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

from django.contrib.auth.decorators import login_required, permission_required

from creme_core.views.generic import view_entity_with_template, list_view, edit_entity

from recurrents.models import RecurrentGenerator
from recurrents.forms.recurrentgenerator import RecurrentGeneratorWizard, RecurrentGeneratorEditForm


_wizard = RecurrentGeneratorWizard()

@login_required
@permission_required('recurrents')
@permission_required('recurrents.add_recurrentgenerator')
def add(request):
    return _wizard(request)

def edit(request, generator_id):
    return edit_entity(request, generator_id, RecurrentGenerator, RecurrentGeneratorEditForm, 'recurrents')

@login_required
@permission_required('recurrents')
def listview(request):
    return list_view(request, RecurrentGenerator, extra_dict={'add_url': '/recurrents/generator/add'})

@login_required
@permission_required('recurrents')
def detailview(request, generator_id):
    return view_entity_with_template(request, generator_id, RecurrentGenerator,
                                     '/recurrents/generator', 'recurrents/view_generator.html',)
