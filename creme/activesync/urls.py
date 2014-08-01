# -*- coding: utf-8 -*-

from django.conf.urls import patterns


urlpatterns = patterns('creme.activesync.views',
    (r'^user_settings$', 'user_settings.edit_own_mobile_settings'),
    (r'^sync$', 'sync.main_sync'),
    #Mobile synchronization configuration
    (r'^mobile_synchronization/edit$', 'mobile_sync.edit'),
)
