# -*- coding: utf-8 -*-

################################################################################
#    Creme is a free/open-source Customer Relationship Management software
#    Copyright (C) 2009-2017  Hybird
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

from json import dumps as json_dump
import warnings

from django.core.exceptions import PermissionDenied
from django.forms.formsets import formset_factory
from django.http import Http404, HttpResponse
from django.utils.translation import ugettext as _

from ..auth.decorators import login_required
from ..gui.quick_forms import quickforms_registry
from ..utils import get_ct_or_404
from .generic import inner_popup


# TODO: it seems there is a problem with formsets : if the 'user' field is empty
#       it does not raise a Validation exception, but it causes a SQL integrity
#       error ; we are saved by the 'empty_label=None' of user field, but it is
#       not really perfect...

@login_required
def add(request, ct_id, count):
    if count == '0':
        raise Http404('Count must be between 1 & 9')

    model = get_ct_or_404(ct_id).model_class()
    model_name = model._meta.verbose_name
    user = request.user

    if not user.has_perm_to_create(model):
        # TODO: manage/display error on js side (for now it just does nothing)
        raise PermissionDenied('You are not allowed to create entity with type "%s"' % model_name)

    base_form_class = quickforms_registry.get_form(model)

    if base_form_class is None:
        raise Http404('No form registered for model: %s' % model)

    # We had the mandatory 'user' argument
    class _QuickForm(base_form_class):
        def __init__(self, *args, **kwargs):
            super(_QuickForm, self).__init__(user=user, *args, **kwargs)
            # HACK : empty_permitted attribute allows formset to remove fields data that hasn't change from initial.
            # This behaviour force user_id value to null when form is empty and causes an SQL integrity error.
            # In django 1.3 empty_permitted cannot be set correctly so force it.
            self.empty_permitted = False

    qformset_class = formset_factory(_QuickForm, extra=int(count))

    if request.method == 'POST':
        qformset = qformset_class(data=request.POST, files=request.FILES or None)

        if qformset.is_valid():
            # for form in qformset.forms:
            for form in qformset:
                form.save()
    else:
        qformset = qformset_class()

    return inner_popup(request, 'creme_core/generics/blockformset/add_popup.html',
                       {'formset': qformset,
                        'title':   _(u'Quick creation of «%s»') % model_name,
                       },
                       is_valid=qformset.is_valid(),
                       reload=False,
                       delegate_reload=True,
                      )


def json_quickform_response(instance):
    response = {'value': instance.id,
                'added': [(instance.id, unicode(instance))],
               }

    return HttpResponse(u'<json>%s</json>' % json_dump(response),
                        content_type="text/html",
                       )


@login_required
def add_from_widget(request, ct_id, count=None):
# def add_from_widget(request, ct_id):  TODO: in creme 1.8
    if count is not None:
        warnings.warn('add_from_widget(): the argument "count" is deprecated.', DeprecationWarning)

    model = get_ct_or_404(ct_id).model_class()
    model_name = model._meta.verbose_name
    user = request.user

    if not user.has_perm_to_create(model):
        # TODO: manage/display error on JS side (for now it just does nothing)
        raise PermissionDenied(u'You are not allowed to create entity with type "%s"' % model_name)

    form_class = quickforms_registry.get_form(model)

    if form_class is None:
        raise Http404('No form registered for model: %s' % model)

    if request.method == 'POST':
        form = form_class(user=user, data=request.POST, files=request.FILES or None, initial=None)

        if form.is_valid():
            form.save()

            return json_quickform_response(form.instance)
    else:
        form = form_class(user=user, initial=None)

    # TODO: 'creme_core/generics/blockform/add_popup2.html' ??
    return inner_popup(request, 'creme_core/generics/form/add_innerpopup.html',
                       {'form':   form,
                        'title':  model.creation_label,
                        'submit_label': model.save_label,
                       },
                       is_valid=form.is_valid(),
                       reload=False,
                       delegate_reload=True,
                      )
