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

from django.conf import settings
from django.utils.timezone import now

from creme import __version__

from .gui.block import BlocksManager
from .models import FieldsConfig
from .utils.media import get_current_theme, get_current_theme_vb


def get_logo_url(request):
    return {'logo_url': settings.LOGO_URL}


def get_css_theme(request):
    current_theme = get_current_theme()

    return {'THEME_NAME':         current_theme,
            'DEFAULT_THEME':      settings.DEFAULT_THEME,
            'THEME_VERBOSE_NAME': get_current_theme_vb(current_theme),
           }


def get_today(request):
    return {'today': now()}


def get_blocks_manager(request):
    return {BlocksManager.var_name: BlocksManager()}


def get_fields_configs(request):
    return {'fields_configs': FieldsConfig.LocalCache()}


def get_version(request):
    return {'creme_version': __version__}


def get_django_version(request):
    if settings.DEBUG:
        from django import get_version
        return {'django_version': get_version()}
    return {}
