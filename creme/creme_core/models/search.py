# -*- coding: utf-8 -*-

################################################################################
#    Creme is a free/open-source Customer Relationship Management software
#    Copyright (C) 2009-2013  Hybird
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

from collections import defaultdict
from functools import partial
import logging

from django.db.models import CharField, ForeignKey, PositiveIntegerField, Q, FieldDoesNotExist
from django.utils.translation import ugettext_lazy as _, ugettext
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType

from ..utils.meta import get_verbose_field_name, ModelFieldEnumerator #get_model_field_info
from .base import CremeModel
from .fields import CTypeForeignKey


logger = logging.getLogger(__name__)


class SearchConfigItem(CremeModel):
    #content_type = ForeignKey(ContentType, verbose_name=_(u"Related type"))
    content_type = CTypeForeignKey(verbose_name=_(u"Related type"))
#    role         = ForeignKey(UserRole, verbose_name=_(u"Related role"), null=True) #TODO:To be done ?
    user         = ForeignKey(User, verbose_name=_(u"Related user"), null=True)

    _searchfields = None
    EXCLUDED_FIELDS_TYPES = frozenset(['DateTimeField', 'DateField', 'FileField', 'ImageField'])

    class Meta:
        app_label = 'creme_core'
        verbose_name = _(u'Search')
        verbose_name_plural = _(u'Searches')

    def __unicode__(self):
        return ugettext(u'Search configuration of "%(user)s" for "%(type)s"') % {
                    'user': self.user or ugettext(u'all users'),
                    'type': self.content_type,
                }

    @staticmethod
    def _get_modelfields_choices(model):
        excluded = SearchConfigItem.EXCLUDED_FIELDS_TYPES
        return ModelFieldEnumerator(model, deep=1) \
                .filter(viewable=True) \
                .exclude(lambda f: f.get_internal_type() in excluded) \
                .choices()

    @property
    def searchfields(self):
        if self._searchfields is None:
            self._searchfields = sfields = []
            append = sfields.append
            ##model = ContentType.objects.get_for_id(self.content_type_id).model_class()
            #model = self.content_type.model_class()

            for sfield in SearchField.objects.filter(search_config_item=self):
                sfield.search_config_item = self #avoids query in SearchField.__unicode__

                try:
                    #get_model_field_info(model, sfield.field, silent=False)
                    unicode(sfield)
                except FieldDoesNotExist as e:
                    logger.warn('%s => SearchField instance removed', e)
                    sfield.delete()
                else:
                    append(sfield)

        return self._searchfields

    def get_modelfields_choices(self):
        """Return a list of tuples (useful for Select.choices) representing
        Fields that can be chosen by the user.
        """
        return self._get_modelfields_choices(self.content_type.model_class())

    @staticmethod
    def create_if_needed(model, fields, user=None):
        """Create a config item & its fields if one does not already exists.
        SearchConfigItem.create_if_needed(SomeDjangoModel, ['SomeDjangoModel_field1', 'SomeDjangoModel_field2', ..])
        """
        ct = ContentType.objects.get_for_model(model)
        sci, created = SearchConfigItem.objects.get_or_create(content_type=ct, user=user)

        if created:
            create_sf = partial(SearchField.objects.create, search_config_item=sci)
            i = 1

            for field in fields:
                verbose_name = get_verbose_field_name(model, field)

                if verbose_name:
                    create_sf(field=field, order=i, field_verbose_name=verbose_name)
                    i += 1
                else:
                    logger.warn('SearchConfigItem.create_if_needed(): invalid field "%s"', field)

        return sci

    @staticmethod
    def get_searchfields_4_model(model, user):
        "Get the list of SearchField instances corresponding to the given model"
        sc_items = SearchConfigItem.objects.filter(content_type=ContentType.objects.get_for_model(model)) \
                                           .filter(Q(user=user) | Q(user__isnull=True)) \
                                           .order_by('-user') #config of the user has higher priority than default one

        for sc_item in sc_items:
            fields = sc_item.searchfields
            if fields:
                fields = list(fields)
                break
        else: #Fallback
            fields = [_FakeSearchField(field=name, field_verbose_name=verbose_name, order=i)
                        for i, (name, verbose_name) in enumerate(SearchConfigItem._get_modelfields_choices(model))
                     ]

        return fields

    @staticmethod
    def populate_searchfields(search_config_items):
        #list(search_config_items) is needed because of mysql
        all_searchfields = SearchField.objects.filter(search_config_item__in=list(search_config_items))
        sfci_dict = defaultdict(list)

        for sf in all_searchfields:
            sfci_dict[sf.search_config_item_id].append(sf)

        for sfci in search_config_items:
            #sfci._searchfields = sfci_dict[sfci.id]
            sfci._searchfields = sfields = sfci_dict[sfci.id]
            for sfield in sfields:
                sfield.search_config_item = sfci #avoids query in SearchField.__unicode__


#TODO: remove this model and store fields in a TextField in SearchConfigItem
class SearchField(CremeModel):
    field              = CharField(_(u"Field"), max_length=100)
    field_verbose_name = CharField(_(u"Field (long name)"), max_length=100) #TODO: not used any more
    search_config_item = ForeignKey(SearchConfigItem, verbose_name=_(u"Associated configuration"))
    order              = PositiveIntegerField(_(u"Priority"))

    class Meta:
        app_label = 'creme_core'
        verbose_name = _(u'Search field')
        verbose_name_plural = _(u'Search fields')
        ordering = ('order',)

    def __unicode__(self):
        "@throws FieldDoesNotExist"
        #return self.field_verbose_name
        model = self.search_config_item.content_type.model_class()
        return get_verbose_field_name(model, self.field, silent=False)


class _FakeSearchField(object):
    def __init__(self, field, field_verbose_name, order):
        self.field = field
        self.field_verbose_name = field_verbose_name
        self.order = order

    def __unicode__(self):
        return self.field_verbose_name
