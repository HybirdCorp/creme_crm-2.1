# -*- coding: utf-8 -*-

from django.conf.urls.defaults import patterns


urlpatterns = patterns('documents.views',
    (r'^$', 'portal.portal'),

    (r'^folders$',                        'folder.listview'),
    (r'^folder/add$',                     'folder.add'),
    (r'^folder/edit/(?P<folder_id>\d+)$', 'folder.edit'),
    (r'^folder/(?P<folder_id>\d+)$',      'folder.detailview'),

    (r'^getChildFolders/$',   'ajax.get_child_folders'),
    (r'^getChildDocuments/$', 'ajax.get_child_documents'),

    (r'^documents$',                          'document.listview'),
    (r'^document/add$',                       'document.add'),
    (r'^document/add_from_detailview$',       'document.add_from_detailview'),
    (r'^document/edit/(?P<document_id>\d+)$', 'document.edit'),
    (r'^document/(?P<object_id>\d+)$',        'document.detailview'),
)
