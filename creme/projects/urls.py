# -*- coding: utf-8 -*-

from django.conf.urls import patterns

urlpatterns = patterns('creme.projects.views',
    (r'^$', 'portal.portal'),

    # TODO : Define what user could do or not if projet is 'close' (with the use of the buttom that sets an effective end date)
    #Project : button for effective end date of project
    (r'^projects$',                           'project.listview'),
    (r'^project/add$',                        'project.add'),
    (r'^project/edit/(?P<project_id>\d+)$',   'project.edit'),
    (r'^project/(?P<project_id>\d+)$',        'project.detailview'),
    (r'^project/(?P<project_id>\d+)/close$',  'project.close'), #TODO: change url ?? project/close/(?P<project_id>\d+)

    #Project: Task block
    (r'^project/(?P<project_id>\d+)/task/add', 'task.add'),
#    (r'^task/delete$',                         'task.delete'),
#    (r'^task/(?P<object_id>\d+)$',             'task.detailview'),
    (r'^task/(?P<task_id>\d+)$',               'task.detailview'),
    (r'^task/edit/(?P<task_id>\d+)$',          'task.edit'),
    (r'^task/edit/(?P<task_id>\d+)/popup$',    'task.edit_popup'),#TODO: Merge with edit ?
    (r'^task/parent/delete$',                  'task.delete_parent'),

    #Task: Parent tasks block
    (r'^task/(?P<task_id>\d+)/parent/add$', 'task.add_parent'),

    #Task: Resource block
    (r'^task/(?P<task_id>\d+)/resource/add$',  'resource.add'),
    (r'^resource/edit/(?P<resource_id>\d+)$',  'resource.edit'),
    (r'^resource/delete$',                     'resource.delete'),

    #Task: Working periods block
#    (r'^task/(?P<task_id>\d+)/period/add$', 'workingperiod.add'),
#    (r'^period/edit/(?P<period_id>\d+)$',   'workingperiod.edit'),
#    (r'^period/delete$',                    'workingperiod.delete'),
    (r'^task/(?P<task_id>\d+)/activity/add$', 'task.add_activity'),
    (r'^activity/edit/(?P<activity_id>\d+)$', 'task.edit_activity'),
    (r'^activity/delete$',                    'task.delete_activity'),
)
