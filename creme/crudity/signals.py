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

from django.contrib.auth import get_user_model

from .constants import SETTING_CRUDITY_SANDBOX_BY_USER


def post_save_setting_value(sender, instance, **kwargs):
    """Set is_sandbox_by_user value on CreateFromEmailBackend subclasses because they are singletons"""
    from .registry import crudity_registry
    from .models import WaitingAction

    if instance.key_id == SETTING_CRUDITY_SANDBOX_BY_USER:
        fetchers = crudity_registry.get_fetchers()
        inputs = []
        for fetcher in fetchers:
            for inputs_dict in fetcher.get_inputs():
                inputs.extend(inputs_dict.values())

        backends = []
        for input in inputs:
            backends.extend(input.get_backends())

        for backend in backends:
            backend.is_sandbox_by_user = instance.value

        if instance.value:
#            WaitingAction.objects.filter(user=None).update(user=User.objects.filter(is_superuser=True).order_by('-pk')[0])

            #TODO: move to a method in User's manager
            user_qs = get_user_model().objects.order_by('id')
            try:
                user = user_qs.filter(is_superuser=True, is_staff=False)[0]
            except IndexError:
                try:
                    user = user_qs.filter(is_superuser=True)[0]
                except IndexError:
                    user = user_qs[0]

            WaitingAction.objects.filter(user=None).update(user=user)
