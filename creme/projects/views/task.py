# -*- coding: utf-8 -*-

################################################################################
#    Creme is a free/open-source Customer Relationship Management software
#    Copyright (C) 2009-2019  Hybird
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
# import warnings

from django.db.models import ProtectedError, Q
from django.db.transaction import atomic
# from django.http import HttpResponse
# from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _  # gettext

from creme.creme_core.auth import build_creation_perm as cperm
# from creme.creme_core.auth.decorators import login_required, permission_required
from creme.creme_core.core.exceptions import ConflictError
from creme.creme_core.models import Relation
from creme.creme_core.utils import get_from_POST_or_404
from creme.creme_core.views import generic

from creme.activities import get_activity_model

from creme import projects
from ..constants import REL_SUB_PART_AS_RESOURCE, REL_SUB_LINKED_2_PTASK
from ..forms import task as task_forms

logger = logging.getLogger(__name__)
Activity = get_activity_model()
ProjectTask = projects.get_task_model()


# def abstract_add_ptask(request, project_id, form=task_forms.TaskCreateForm,
#                        title=_('Create a task for «%s»'),
#                        submit_label=ProjectTask.save_label,
#                       ):
#     warnings.warn('projects.views.task.abstract_add_ptask() is deprecated ; '
#                   'use the class-based view TaskCreation instead.',
#                   DeprecationWarning
#                  )
#     return generic.add_to_entity(request, project_id, form, title,
#                                  entity_class=projects.get_project_model(),
#                                  submit_label=submit_label,
#                                 )


# def abstract_edit_ptask(request, task_id, form=task_forms.TaskEditForm):
#     warnings.warn('projects.views.task.abstract_edit_ptask() is deprecated ; '
#                   'use the class-based view TaskEdition instead.',
#                   DeprecationWarning
#                  )
#     return generic.edit_entity(request, task_id, ProjectTask, form)


# def abstract_edit_ptask_popup(request, task_id, form=task_forms.TaskEditForm):
#     warnings.warn('projects.views.task.abstract_edit_ptask_popup() is deprecated ; '
#                   'use the class-based view TaskEditionPopup instead.',
#                   DeprecationWarning
#                  )
#     return generic.edit_model_with_popup(request, {'pk': task_id}, ProjectTask, form)


# def abstract_view_ptask(request, task_id,
#                         template='projects/view_task.html',
#                        ):
#     warnings.warn('projects.views.task.abstract_view_ptask() is deprecated ; '
#                   'use the class-based view TaskDetail instead.',
#                   DeprecationWarning
#                  )
#     return generic.view_entity(request, task_id, ProjectTask, template=template)


# @login_required
# @permission_required(('projects', cperm(ProjectTask)))
# def add(request, project_id):
#     warnings.warn('projects.views.task.add() is deprecated.', DeprecationWarning)
#     return abstract_add_ptask(request, project_id)


# @login_required
# @permission_required('projects')
# def detailview(request, task_id):
#     warnings.warn('projects.views.task.detailview() is deprecated.', DeprecationWarning)
#     return abstract_view_ptask(request, task_id)


# @login_required
# @permission_required('projects')
# def edit(request, task_id):
#     warnings.warn('projects.views.task.edit() is deprecated.', DeprecationWarning)
#     return abstract_edit_ptask(request, task_id)


# @login_required
# @permission_required('projects')
# def edit_popup(request, task_id):
#     warnings.warn('projects.views.task.edit_popup() is deprecated.', DeprecationWarning)
#     return abstract_edit_ptask_popup(request, task_id)


# @login_required
# @permission_required('projects')
# def delete_parent(request):
#     POST = request.POST
#     parent_id = get_from_POST_or_404(POST, 'parent_id')
#     task = get_object_or_404(ProjectTask, pk=get_from_POST_or_404(POST, 'id'))
#     user = request.user
#
#     # user.has_perm_to_change_or_die(task.project) #beware: modify block_tasks.html template if uncommented....
#     user.has_perm_to_change_or_die(task)
#
#     task.parent_tasks.remove(parent_id)
#
#     return HttpResponse()


# Class-based views  ----------------------------------------------------------

class TaskCreation(generic.AddingInstanceToEntityPopup):
    model = ProjectTask
    form_class = task_forms.TaskCreateForm
    title = _('Create a task for «{entity}»')
    entity_id_url_kwarg = 'project_id'
    entity_classes = projects.get_project_model()

    def check_view_permissions(self, user):
        super().check_view_permissions(user=user)
        self.request.user.has_perm_to_create_or_die(ProjectTask)


class TaskDetail(generic.EntityDetail):
    model = ProjectTask
    template_name = 'projects/view_task.html'
    pk_url_kwarg = 'task_id'


class TaskEdition(generic.EntityEdition):
    model = ProjectTask
    form_class = task_forms.TaskEditForm
    pk_url_kwarg = 'task_id'


class TaskEditionPopup(generic.EntityEditionPopup):
    model = ProjectTask
    form_class = task_forms.TaskEditForm
    pk_url_kwarg = 'task_id'


class ParentsAdding(generic.EntityEditionPopup):
    model = ProjectTask
    form_class = task_forms.TaskAddParentForm
    pk_url_kwarg = 'task_id'
    title = _('Adding parents to «{object}»')


class ParentRemoving(generic.base.EntityRelatedMixin, generic.CremeDeletion):
    permissions = 'projects'
    entity_classes = ProjectTask

    task_id_arg = 'id'
    parent_id_arg = 'parent_id'

    def get_related_entity_id(self):
        return get_from_POST_or_404(self.request.POST, self.task_id_arg, cast=int)

    def perform_deletion(self, request):
        parent_id = get_from_POST_or_404(request.POST, self.parent_id_arg)
        self.get_related_entity().parent_tasks.remove(parent_id)


class ActivityEditionPopup(generic.EntityEditionPopup):
    model = Activity
    # NB: the form checks that the Activity is related to a task
    form_class = task_forms.RelatedActivityEditForm
    pk_url_kwarg = 'activity_id'


# Activities -------------------------------------------------------------------

# def abstract_edit_activity(request, activity_id, form=task_forms.RelatedActivityEditForm):
#     warnings.warn('projects.views.task.abstract_edit_activity() is deprecated ; '
#                   'use the class-based view ActivityEditionPopup instead.',
#                   DeprecationWarning
#                  )
#     return generic.edit_model_with_popup(request, {'pk': activity_id}, Activity, form)


# TODO: LINK perm instead of CHANGE ?
class RelatedActivityCreation(generic.AddingInstanceToEntityPopup):
    model = Activity
    form_class = task_forms.RelatedActivityCreateForm
    permissions = cperm(Activity)
    title = _('New activity related to «{entity}»')
    entity_id_url_kwarg = 'task_id'
    entity_classes = ProjectTask


# @login_required
# @permission_required('projects')
# def edit_activity(request, activity_id):
#     warnings.warn('projects.views.task.edit_activity() is deprecated.', DeprecationWarning)
#     return abstract_edit_activity(request, activity_id)


# @login_required
# @permission_required('projects')
# def delete_activity(request):
#     activity = get_object_or_404(Activity, pk=request.POST.get('id'))
#     get_rel = Relation.objects.get
#
#     try:
#         rel1 = get_rel(type=constants.REL_SUB_PART_AS_RESOURCE, object_entity=activity)
#         rel2 = get_rel(subject_entity=activity, type=constants.REL_SUB_LINKED_2_PTASK)
#     except Relation.DoesNotExist as e:
#         raise ConflictError('This activity is not related to a project task.') from e
#
#     request.user.has_perm_to_change_or_die(rel2.object_entity.get_real_entity())  # Project task
#
#     try:
#         with atomic():
#             rel1.delete()
#             rel2.delete()
#             activity.delete()
#     except ProtectedError:
#         logger.exception('Error when deleting an activity of project')
#         status = 409
#         msg = gettext('Can not be deleted because of its dependencies.')
#     except Exception as e:
#         status = 400
#         msg = gettext('The deletion caused an unexpected error [{}].').format(e)
#     else:
#         msg = gettext('Operation successfully completed')
#         status = 200
#
#     return HttpResponse(msg, status=status)
class ActivityDeletion(generic.CremeModelDeletion):
    model = Activity
    permissions = 'projects'

    def get_relations(self, activity):
        relations = {
            r.type_id: r
                for r in Relation.objects
                                 .filter(Q(type=REL_SUB_PART_AS_RESOURCE, object_entity=activity) |
                                         Q(subject_entity=activity, type=REL_SUB_LINKED_2_PTASK)
                                        )[:2]
        }

        ptask_rel = relations.get(REL_SUB_LINKED_2_PTASK)

        if ptask_rel is None or REL_SUB_PART_AS_RESOURCE not in relations:
            raise ConflictError('This activity is not related to a project task.')

        # TODO: unit test
        self.request.user.has_perm_to_change_or_die(ptask_rel.object_entity.get_real_entity())  # Project task

        return relations

    def perform_deletion(self, request):
        activity = self.object = self.get_object()
        relations = self.get_relations(activity)

        try:
            with atomic():
                for rel in relations.values():
                    rel.delete()

                activity.delete()
        except ProtectedError as e:
            logger.exception('Error when deleting an activity of project')

            raise ConflictError('Can not be deleted because of its dependencies.') from e
