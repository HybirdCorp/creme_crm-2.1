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

import warnings

from django.conf import settings
from django.template import Library
from django.utils.html import escape

from ..constants import ICON_SIZE_MAP
from ..gui.icon_registry import icon_registry
from ..utils.media import get_creme_media_url


register = Library()


@register.inclusion_tag('creme_core/templatetags/widgets/add_button.html', takes_context=True)
def get_add_button(context, entity, user):
    url = entity.get_create_absolute_url()

    if not url:
        path = context.get('path')

        if path:
            warnings.warn("get_add_button(): 'path' in context is deprecated ; "
                          "set a method get_create_absolute_url() in you model instead.",
                          DeprecationWarning
                         )
            url = '%s/add' % path

    context['url'] = url  # TODO: in template ({% with ... %}) when 'path' is not supported anymore.
    context['can_add'] = user.has_perm_to_create(entity)

    return context


@register.inclusion_tag('creme_core/templatetags/widgets/delete_button.html', takes_context=True)
def get_delete_button(context, entity, user):
    context['can_delete'] = user.has_perm_to_delete(entity)
    return context


@register.inclusion_tag('creme_core/templatetags/widgets/restore_button.html', takes_context=True)
def get_restore_button(context, entity, user):  # TODO: factorise
    context['can_delete'] = user.has_perm_to_delete(entity)
    return context


@register.inclusion_tag('creme_core/templatetags/widgets/edit_button.html', takes_context=True)
def get_edit_button(context, entity, user):
    context['can_change'] = user.has_perm_to_change(entity)
    return context


@register.inclusion_tag('creme_core/templatetags/widgets/clone_button.html', takes_context=True)
def get_clone_button(context, entity, user):
    context['can_create'] = user.has_perm_to_create(entity)
    return context


@register.inclusion_tag('creme_core/templatetags/widgets/entity_actions.html', takes_context=True)
def get_entity_actions(context, entity):
    user = context['user']

    context['id'] = entity.id  # TODO: new context VS object.id
    context['actions'] = entity.get_actions(user)

    return context


@register.simple_tag
def widget_hyperlink(instance):
    """{% widget_hyperlink my_instance %}
    @param instance Instance of DjangoModel which has a get_absolute_url() method
           & should have overload its __unicode__() method too.
           BEWARE: it must not be a CremeEntity instance, or an auxiliary instance,
           because the permissions are not checked.
    """
    return u'<a href="%s">%s</a>' % (instance.get_absolute_url(), escape(instance))


@register.simple_tag
def widget_entity_hyperlink(entity, user, ignore_deleted=False):  # TODO: takes_context for user ???
    "{% widget_entity_hyperlink my_entity user %}"
    if user.has_perm_to_view(entity):
        return u'<a href="%s"%s>%s</a>' % (
                        entity.get_absolute_url(),
                        ' class="is_deleted"' if entity.is_deleted and not ignore_deleted else '',
                        escape(entity)
                    )

    return settings.HIDDEN_VALUE


# TODO: use in forbidden.html
# @register.inclusion_tag('creme_core/templatetags/widgets/list_instances.html')
# def widget_list_instances(instances, user):
#     return {'objects': instances, 'user': user}

@register.inclusion_tag('creme_core/templatetags/widgets/select_or_msg.html')
def widget_select_or_msg(items, void_msg):
    return {'items': items, 'void_msg': void_msg}


def _get_image_path_for_model(theme, model, size):
    path = icon_registry.get(model, ICON_SIZE_MAP[size])

    if not path:
        return ''

    try:
        path = get_creme_media_url(theme, path)
    except KeyError:
        path = ''

    return path


def _get_image_for_model(theme, model, size):
    path = _get_image_path_for_model(theme, model, size)
    return u'<img src="%(src)s" alt="%(title)s" title="%(title)s" />' % {
                    'src':   path,
                    'title': model._meta.verbose_name,
                }


@register.simple_tag(takes_context=True)
def get_image_for_object(context, obj, size):  # TODO: size='default' ??
    """{% get_image_for_object object 'big' %}"""
    return _get_image_for_model(context['THEME_NAME'], obj.__class__, size)


@register.simple_tag(takes_context=True)
def get_image_for_ctype(context, ctype, size):
    """{% get_image_for_ctype ctype 'small' %}"""
    return _get_image_for_model(context['THEME_NAME'], ctype.model_class(), size)


@register.simple_tag(takes_context=True)
def get_image_path_for_ctype(context, ctype, size):
    """{% get_image_path_for_ctype ctype 'small' %}"""
    return _get_image_path_for_model(context['THEME_NAME'], ctype.model_class(), size)
