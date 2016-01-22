# -*- coding: utf-8 -*-

################################################################################
#    Creme is a free/open-source Customer Relationship Management software
#    Copyright (C) 2009-2014  Hybird
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

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.shortcuts import render
from django.utils.translation import ugettext as _

from creme.creme_core.auth.decorators import login_required


# TODO: remove 'models' arg (and use app_name to get the related contenttypes) ??
@login_required
def app_portal(request, app_name, template, models, stats, config_url=None, extra_template_dict=None):
    has_perm = request.user.has_perm

    if not has_perm(app_name):
        raise PermissionDenied(_(u'You are not allowed to access to the app: %s') % app_name)

    get_ct = ContentType.objects.get_for_model

    try:
        ct_ids = [get_ct(model).id for model in models]
    except TypeError:  # 'models' is a not a sequence -> CremeEntity
        ct_ids = [get_ct(models).id]

    template_dict = {'app_name':     app_name,
                     'ct_ids':       ct_ids,
                     'stats':        stats,
                     'config_url':   config_url,
                     'can_admin':    has_perm('%s.can_admin' % app_name),
                    }

    if extra_template_dict is not None:
        template_dict.update(extra_template_dict)

    return render(request, template, template_dict)
