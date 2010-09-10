# -*- coding: utf-8 -*-

################################################################################
#    Creme is a free/open-source Customer Relationship Management software
#    Copyright (C) 2009-2010  Hybird
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

from django.utils.translation import ugettext as _
from django.contrib.contenttypes.models import ContentType

from creme_core.models.header_filter import HeaderFilterItem, HeaderFilter, HFI_FIELD
from creme_core.models import RelationType, BlockConfigItem, ButtonMenuItem, SearchConfigItem, SearchField
from creme_core.utils import create_or_update_models_instance as create
from creme_core.utils.meta import get_verbose_field_name
from creme_core.management.commands.creme_populate import BasePopulator

from creme_config.models import CremeKVConfig

from persons.models import Contact, Organisation

from products.models import Product, Service

from billing.models import SalesOrder, Invoice, Quote

from opportunities.models import SalesPhase, Origin, Opportunity
from opportunities.buttons import linked_opportunity_button
from opportunities.constants import *


class Populator(BasePopulator):
    dependencies = ['creme.core', 'creme.config', 'creme.persons', 'creme.products', 'creme.billing']

    def populate(self, *args, **kwargs):
        RelationType.create((REL_SUB_TARGETS_ORGA,      _(u'targets the organisation'),          [Opportunity]),
                            (REL_OBJ_TARGETS_ORGA,      _(u"targeted by the opportunity")))
        RelationType.create((REL_SUB_LINKED_PRODUCT,    _(u"is linked to the opportunity"),      [Product]),
                            (REL_OBJ_LINKED_PRODUCT,    _(u"concerns the product"),              [Opportunity]))
        RelationType.create((REL_SUB_LINKED_SERVICE,    _(u"is linked to the opportunity"),      [Service]),
                            (REL_OBJ_LINKED_SERVICE,    _(u"concerns the service"),              [Opportunity]))
        RelationType.create((REL_SUB_LINKED_CONTACT,    _(u"involves in the opportunity"),       [Contact]),
                            (REL_OBJ_LINKED_CONTACT,    _(u"stages"),                            [Opportunity]))
        RelationType.create((REL_SUB_LINKED_SALESORDER, _(u"is associate with the opportunity"), [SalesOrder]),
                            (REL_OBJ_LINKED_SALESORDER, _(u"has generated the salesorder"),      [Opportunity]))
        RelationType.create((REL_SUB_LINKED_INVOICE,    _(u"generated for the opportunity"),     [Invoice]),
                            (REL_OBJ_LINKED_INVOICE,    _(u"has resulted in the invoice"),       [Opportunity]))
        RelationType.create((REL_SUB_LINKED_QUOTE,      _(u"generated for the opportunity"),     [Quote]),
                            (REL_OBJ_LINKED_QUOTE,      _(u"has resulted in the quote"),         [Opportunity]))
        RelationType.create((REL_SUB_RESPONSIBLE,       _(u"is responsible for"),                [Contact]),
                            (REL_OBJ_RESPONSIBLE,       _(u"has as responsible contact"),        [Opportunity]))
        RelationType.create((REL_SUB_EMIT_ORGA,         _(u"has generated the opportunity"),     [Organisation]),
                            (REL_OBJ_EMIT_ORGA,         _(u"has been generated by"),             [Opportunity]))


        create(CremeKVConfig, "LINE_IN_OPPORTUNITIES",  value="0")

        create(SalesPhase, 1, name=_(u"Forthcoming"),       description="...")
        create(SalesPhase, 2, name=_(u"Abandoned"),         description="...")
        create(SalesPhase, 3, name=_(u"Won"),               description="...")
        create(SalesPhase, 4, name=_(u"Lost"),              description="...")
        create(SalesPhase, 5, name=_(u"Under negotiation"), description="...")
        create(SalesPhase, 6, name=_(u"In progress"),       description="...")

        create(Origin, 1, name=_(u"None"),             description="...")
        create(Origin, 2, name=_(u"Web site"),         description="...")
        create(Origin, 3, name=_(u"Mouth"),            description="...")
        create(Origin, 4, name=_(u"Show"),             description="...")
        create(Origin, 5, name=_(u"Direct email"),     description="...")
        create(Origin, 6, name=_(u"Direct phonecall"), description="...")
        create(Origin, 7, name=_(u"Employee"),         description="...")
        create(Origin, 8, name=_(u"Partner"),          description="...")
        create(Origin, 9, name=_(u"Other"),            description="...")

        get_ct = ContentType.objects.get_for_model

        hf_id = create(HeaderFilter, 'opportunities-hf', name=_(u"Opportunity view"), entity_type_id=get_ct(Opportunity).id, is_custom=False).id
        pref  = 'opportunities-hfi_'
        create(HeaderFilterItem, pref + 'name',    order=1, name='name',            title=_(u'Name'),            type=HFI_FIELD, header_filter_id=hf_id, has_a_filter=True, editable=True, sortable=True, filter_string="name__icontains")
        create(HeaderFilterItem, pref + 'ref',     order=2, name='reference',       title=_(u'Reference'),      type=HFI_FIELD, header_filter_id=hf_id, has_a_filter=True, editable=True, sortable=True, filter_string="reference__icontains")
        create(HeaderFilterItem, pref + 'phase',   order=3, name='sales_phase',     title=_(u'Sales phase'), type=HFI_FIELD, header_filter_id=hf_id, has_a_filter=True, editable=True, sortable=True, filter_string="sales_phase__name__icontains")
        create(HeaderFilterItem, pref + 'expdate', order=4, name='closing_date', title=_(u'Closing date'),       type=HFI_FIELD, header_filter_id=hf_id, has_a_filter=True, editable=True, sortable=True, filter_string="closing_date__range")

        create(ButtonMenuItem, 'opportunities-linked_opp_button', content_type_id=get_ct(Organisation).id, button_id=linked_opportunity_button.id_, order=30)

        SearchConfigItem.create(Opportunity, ['name', 'made_sales', 'sales_phase__name', 'origin__name'])
