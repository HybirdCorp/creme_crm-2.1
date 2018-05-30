# -*- coding: utf-8 -*-

################################################################################
#    Creme is a free/open-source Customer Relationship Management software
#    Copyright (C) 2009-2018  Hybird
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

# from django.apps import apps
# from django.forms import MultipleChoiceField
# from django.utils import translation
# from django.utils.translation import ugettext_lazy as _
# from django.utils.encoding import force_unicode
#
# # from creme.creme_core.registry import creme_registry
# from creme.creme_core.models import PreferedMenuItem
# from creme.creme_core.forms import CremeForm
# from creme.creme_core.forms.widgets import OrderedMultipleChoiceWidget
# from creme.creme_core.gui.menu import creme_menu
# from creme.creme_core.utils.unicode_collation import collator
#
#
# class PreferedMenuForm(CremeForm):
#     menu_entries = MultipleChoiceField(label=_(u'Menu entries'), required=False, widget=OrderedMultipleChoiceWidget)
#
#     def __init__(self, user2edit, *args, **kwargs):
#         super(PreferedMenuForm, self).__init__(*args, **kwargs)
#         self.user2edit = user2edit
#
#         # get_app = creme_registry.get_app
#         get_app_config = apps.get_app_config
#         has_perm = user2edit.has_perm if user2edit else lambda perm_label: True
#         menu_entries = self.fields['menu_entries']
#         # # menu_entries.choices = sorted(((item.url, u'%s - %s' % (get_app(appitem.app_name).verbose_name, item.name))
#         # menu_entries.choices = sorted(((item.url, u'%s - %s' % (get_app_config(appitem.app_name).verbose_name, item.name))
#         #                                     for appitem in creme_menu
#         #                                         if has_perm(appitem.app_name)
#         #                                             for item in appitem.items
#         #                                                 if has_perm(item.perm)
#         #                               ),
#         #                               key=lambda t: t[1]
#         #                              )
#         choices = [(item.url, u'%s - %s' % (get_app_config(app_item.app_name).verbose_name, item.name))
#                         for app_item in creme_menu
#                             if has_perm(app_item.app_name)
#                                 for item in app_item.items
#                                     if has_perm(item.perm)
#                   ]
#
#         sort_key = collator.sort_key
#         choices.sort(key=lambda c: sort_key(c[1]))
#
#         menu_entries.choices = choices
#         menu_entries.initial = PreferedMenuItem.objects.filter(user=user2edit) \
#                                                        .order_by('order') \
#                                                        .values_list('url', flat=True)
#
#     def save(self):
#         user = self.user2edit
#
#         PreferedMenuItem.objects.filter(user=user).delete()
#
#         create_item   = PreferedMenuItem.objects.create
#         get_item_name = creme_menu.get_item_name
#
#         # NB: the default PreferedMenuItem items (user==None) will be before other ones.
#         offset = 100 if user else 1
#
#         # NB: the technic used to retrieve translation key is the one used by Meta classes (verbose_name_raw) (can be improved ??)
#         lang = translation.get_language()
#         translation.deactivate_all()
#
#         for i, item_url in enumerate(self.cleaned_data['menu_entries']):
#             create_item(user=user, label=force_unicode(get_item_name(item_url)), url=item_url, order=i + offset)
#
#         translation.activate(lang)
