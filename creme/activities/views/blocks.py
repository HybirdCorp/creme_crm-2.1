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

from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import ugettext as _

from creme.creme_core.auth.decorators import login_required, permission_required
from creme.creme_core.models import Relation, CremeEntity
from creme.creme_core.views.generic import add_to_entity
from creme.creme_core.utils import get_from_POST_or_404

from .. import get_activity_model
from ..models import Activity
from ..forms.blocks import ParticipantCreateForm, SubjectCreateForm
from ..constants import (REL_SUB_PART_2_ACTIVITY, REL_OBJ_PART_2_ACTIVITY,
        REL_SUB_ACTIVITY_SUBJECT, REL_SUB_LINKED_2_ACTIVITY)


Activity = get_activity_model()

@login_required
@permission_required('activities')
def add_participant(request, activity_id):
    return add_to_entity(request, activity_id, ParticipantCreateForm,
                         _(u'Adding participants to activity <%s>'),
                         entity_class=Activity, link_perm=True,
                        )

@login_required
@permission_required('activities')
def delete_participant(request):
    relation = get_object_or_404(Relation,
                                 pk=get_from_POST_or_404(request.POST, 'id'),
                                 type=REL_OBJ_PART_2_ACTIVITY,
                                )
    subject  = relation.subject_entity
    user     = request.user

    has_perm = user.has_perm_to_unlink_or_die
    has_perm(subject)
    has_perm(relation.object_entity)

    relation.delete()

    return redirect(subject.get_real_entity())

@login_required
@permission_required('activities')
def add_subject(request, activity_id):
    return add_to_entity(request, activity_id, SubjectCreateForm,
                         _(u'Adding subjects to activity <%s>'),
                         entity_class=Activity, link_perm=True,
                        )

@login_required
@permission_required('activities')
def unlink_activity(request):
    POST = request.POST
    activity_id = get_from_POST_or_404(POST, 'id')
    entity_id   = get_from_POST_or_404(POST, 'object_id')
    entities = list(CremeEntity.objects.filter(pk__in=[activity_id, entity_id]))

    if len(entities) != 2:
        raise Http404(_('One entity does not exist any more.'))

    has_perm = request.user.has_perm_to_unlink_or_die

    for entity in entities:
        has_perm(entity)

    types = (REL_SUB_PART_2_ACTIVITY, REL_SUB_ACTIVITY_SUBJECT, REL_SUB_LINKED_2_ACTIVITY)
    for relation in Relation.objects.filter(subject_entity=entity_id, 
                                            type__in=types,
                                            object_entity=activity_id):
        relation.delete()

    return HttpResponse('')
