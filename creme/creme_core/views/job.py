# -*- coding: utf-8 -*-

################################################################################
#    Creme is a free/open-source Customer Relationship Management software
#    Copyright (C) 2016-2019  Hybird
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

from django.db.transaction import atomic
from django.http import HttpResponse, Http404  # HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.http import is_safe_url
from django.utils.translation import gettext_lazy as _, gettext

from ..auth import SUPERUSER_PERM
from ..auth.decorators import login_required, superuser_required  # _check_superuser
from ..bricks import JobBrick
from ..core.exceptions import ConflictError
from ..core.job import JobManagerQueue
from ..models import Job

from . import bricks as bricks_views
from .decorators import jsonify, POST_only

from . import generic


class Jobs(generic.BricksView):
    template_name = 'creme_core/job/list-all.html'
    permissions = SUPERUSER_PERM

    # def check_view_permissions(self, user):
    #     super().check_view_permissions(user=user)
    #     _check_superuser(user)


class MyJobs(generic.BricksView):
    template_name = 'creme_core/job/list-mine.html'


class JobDetail(generic.CremeModelDetail):
    model = Job
    template_name = 'creme_core/job/detail.html'
    pk_url_kwarg = 'job_id'

    def check_instance_permissions(self, instance, user):
        jtype = instance.type

        if jtype is None:
            raise Http404(gettext('Unknown job type ({}). Please contact your administrator.')
                                 .format(instance.id)
                         )

        instance.check_owner_or_die(user)

    def get_list_url(self):
        request = self.request
        list_url = request.GET.get('list_url')
        list_url_is_safe = list_url and is_safe_url(
            url=list_url,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        )

        return list_url if list_url_is_safe else reverse('creme_core__my_jobs')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        job = self.object
        context['results_bricks'] = job.type.results_bricks
        context['bricks_reload_url'] = reverse('creme_core__reload_job_bricks', args=(job.id,))
        context['list_url'] = self.get_list_url()

        return context


class JobEdition(generic.CremeModelEditionPopup):
    model = Job
    # form_class = ...
    pk_url_kwarg = 'job_id'
    permissions = SUPERUSER_PERM
    title = _('Edit the job «{object}»')

    def check_instance_permissions(self, instance, user):
        super().check_instance_permissions(instance=instance, user=user)

        if instance.user_id is not None:
            raise ConflictError('A non-system job cannot be edited')

    # def check_view_permissions(self, user):
    #     super().check_view_permissions(user=user)
    #     _check_superuser(user)

    def get_form_class(self):
        config_form = self.object.get_config_form_class()
        if config_form is None:
            raise ConflictError('This job cannot be edited')

        return config_form


@login_required
@superuser_required
@POST_only
@atomic
def enable(request, job_id, enabled=True):
    job = get_object_or_404(Job.objects.select_for_update(), id=job_id)

    if job.user_id is not None:
        raise ConflictError('A non-system job cannot be disabled')

    job.enabled = enabled
    job.save()

    return HttpResponse()


# @login_required
# @POST_only
# def delete(request, job_id):
#     job = get_object_or_404(Job, id=job_id)
#
#     if job.user_id is None:
#         raise ConflictError('A system job cannot be cleared')
#
#     job.check_owner_or_die(request.user)
#
#     if not job.is_finished:
#         raise ConflictError('A non finished job cannot be cleared')
#
#     job.delete()
#
#     url = request.POST.get('back_url') or reverse('creme_core__my_jobs')
#
#     if request.is_ajax():
#         return HttpResponse(content=url)
#
#     return HttpResponseRedirect(url)
class JobDeletion(generic.CremeModelDeletion):
    model = Job
    job_id_url_kwarg = 'job_id'

    def check_instance_permissions(self, instance, user):
        if instance.user_id is None:
            raise ConflictError('A system job cannot be cleared')

        instance.check_owner_or_die(user)

        if not instance.is_finished:
            raise ConflictError('A non finished job cannot be cleared')

    def get_query_kwargs(self):
        return {'id': self.kwargs[self.job_id_url_kwarg]}

    def get_ajax_success_url(self):
        return self.get_success_url()

    def get_success_url(self):
        return self.request.POST.get('back_url') or reverse('creme_core__my_jobs')


@login_required
@jsonify
def get_info(request):
    info = {}
    queue = JobManagerQueue.get_main_queue()

    error = queue.ping()
    if error is not None:
        info['error'] = error

    job_ids = [int(ji) for ji in request.GET.getlist('id') if ji.isdigit()]

    if job_ids:
        user = request.user
        jobs = Job.objects.in_bulk(job_ids)

        for job_id in job_ids:
            job = jobs.get(job_id)
            if job is None:
                info[job_id] = 'Invalid job ID'
            else:
                if not job.check_owner(user):
                    info[job_id] = 'Job is not allowed'
                else:
                    ack_errors = job.ack_errors

                    # NB: we check 'error' too, to avoid flooding queue/job_manager.
                    if ack_errors and not error:
                        queue_error = queue.start_job(job) if job.user else job.refresh()
                        if not queue_error:
                            job.forget_ack_errors()
                            ack_errors = 0  # TODO: read again from DB ?

                    progress = job.progress

                    info[job_id] = {
                        'status':     job.status,
                        'ack_errors': ack_errors,
                        'progress':   progress.data,
                    }

    return info


@login_required
@jsonify
def reload_bricks(request, job_id):
    brick_ids = bricks_views.get_brick_ids_or_404(request)
    job = get_object_or_404(Job, id=job_id)
    bricks = []
    results_bricks = None

    for brick_id in brick_ids:
        if brick_id == JobBrick.id_:
            bricks.append(JobBrick())
        else:
            if results_bricks is None:
                results_bricks = job.type.results_bricks

            for err_brick in results_bricks:
                if brick_id == err_brick.id_:
                    bricks.append(err_brick)
                    break
            else:
                raise Http404('Invalid brick ID')

    job.check_owner_or_die(request.user)

    return bricks_views.bricks_render_info(request, bricks=bricks,
                                           context=bricks_views.build_context(request, job=job),
                                          )
