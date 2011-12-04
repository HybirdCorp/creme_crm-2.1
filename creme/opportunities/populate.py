# -*- coding: utf-8 -*-

################################################################################
#    Creme is a free/open-source Customer Relationship Management software
#    Copyright (C) 2009-2011  Hybird
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

from logging import info

from django.utils.translation import ugettext as _
from django.conf import settings

from creme_core.models import (RelationType, BlockDetailviewLocation, BlockPortalLocation,
                               ButtonMenuItem, SearchConfigItem, HeaderFilterItem, HeaderFilter,
                               EntityFilterCondition, EntityFilter)
from creme_core.blocks import properties_block, relations_block, customfields_block, history_block
from creme_core.management.commands.creme_populate import BasePopulator

from creme_config.models import SettingKey, SettingValue

from persons.models import Contact, Organisation

from products.models import Product, Service

from billing.models import SalesOrder, Invoice, Quote

from opportunities.models import SalesPhase, Origin, Opportunity
from opportunities.blocks import *
from opportunities.buttons import linked_opportunity_button
from opportunities.constants import *


class Populator(BasePopulator):
    dependencies = ['creme_core', 'creme_config', 'persons', 'products', 'billing']

    def populate(self, *args, **kwargs):
        rt_sub_targets, rt_obj_targets = \
        RelationType.create((REL_SUB_TARGETS,      _(u'targets the organisation/contact'), [Opportunity]),
                            (REL_OBJ_TARGETS,      _(u"targeted by the opportunity"),      [Organisation, Contact]),
                            is_internal=True
                           )
        RelationType.create((REL_SUB_LINKED_PRODUCT,    _(u"is linked to the opportunity"),          [Product]),
                            (REL_OBJ_LINKED_PRODUCT,    _(u"concerns the product"),                  [Opportunity]))
        RelationType.create((REL_SUB_LINKED_SERVICE,    _(u"is linked to the opportunity"),          [Service]),
                            (REL_OBJ_LINKED_SERVICE,    _(u"concerns the service"),                  [Opportunity]))
        RelationType.create((REL_SUB_LINKED_CONTACT,    _(u"involves in the opportunity"),           [Contact]),
                            (REL_OBJ_LINKED_CONTACT,    _(u"stages"),                                [Opportunity]))
        RelationType.create((REL_SUB_LINKED_SALESORDER, _(u"is associate with the opportunity"),     [SalesOrder]),
                            (REL_OBJ_LINKED_SALESORDER, _(u"has generated the salesorder"),          [Opportunity]))
        RelationType.create((REL_SUB_LINKED_INVOICE,    _(u"generated for the opportunity"),         [Invoice]),
                            (REL_OBJ_LINKED_INVOICE,    _(u"has resulted in the invoice"),           [Opportunity]))
        RelationType.create((REL_SUB_LINKED_QUOTE,      _(u"generated for the opportunity"),         [Quote]),
                            (REL_OBJ_LINKED_QUOTE,      _(u"has resulted in the quote"),             [Opportunity]))
        RelationType.create((REL_SUB_RESPONSIBLE,       _(u"is responsible for"),                    [Contact]),
                            (REL_OBJ_RESPONSIBLE,       _(u"has as responsible contact"),            [Opportunity]))
        rt_sub_emit_orga, rt_obj_emit_orga  = \
        RelationType.create((REL_SUB_EMIT_ORGA,         _(u"has generated the opportunity"),         [Organisation]),
                            (REL_OBJ_EMIT_ORGA,         _(u"has been generated by"),                 [Opportunity]))
        RelationType.create((REL_SUB_CURRENT_DOC,       _(u'is the current accounting document of'), [SalesOrder, Invoice, Quote]),
                            (REL_OBJ_CURRENT_DOC,       _(u'has as current accounting document'),    [Opportunity]))

        sk = SettingKey.create(pk=SETTING_USE_LINES,
                               description=_(u"Use Product and Service lines"),
                               app_label='opportunities', type=SettingKey.BOOL
                              )
        SettingValue.create_if_needed(key=sk, user=None, value=False)

        if not SalesPhase.objects.exists():
            create_sphase = SalesPhase.objects.create
            create_sphase(name=_(u"Forthcoming"),       description="...")
            create_sphase(name=_(u"Abandoned"),         description="...")
            won  = create_sphase(name=_(u"Won"),        description="...")
            lost = create_sphase(name=_(u"Lost"),       description="...")
            create_sphase(name=_(u"Under negotiation"), description="...")
            create_sphase(name=_(u"In progress"),       description="...")
        else:
            won = None
            lost = None

        if not Origin.objects.exists():
            create_origin = Origin.objects.create
            create_origin(name=_(u"None"),             description="...")
            create_origin(name=_(u"Web site"),         description="...")
            create_origin(name=_(u"Mouth"),            description="...")
            create_origin(name=_(u"Show"),             description="...")
            create_origin(name=_(u"Direct email"),     description="...")
            create_origin(name=_(u"Direct phonecall"), description="...")
            create_origin(name=_(u"Employee"),         description="...")
            create_origin(name=_(u"Partner"),          description="...")
            create_origin(name=_(u"Other"),            description="...")

        hf = HeaderFilter.create(pk='opportunities-hf', name=_(u'Opportunity view'), model=Opportunity)
        hf.set_items([HeaderFilterItem.build_4_field(model=Opportunity, name='name'),
                      HeaderFilterItem.build_4_relation(rtype=rt_sub_targets),
                      HeaderFilterItem.build_4_field(model=Opportunity, name='sales_phase'),
                      HeaderFilterItem.build_4_field(model=Opportunity, name='estimated_sales'),
                      HeaderFilterItem.build_4_field(model=Opportunity, name='made_sales'),
                      HeaderFilterItem.build_4_field(model=Opportunity, name='expected_closing_date'),
                     ])

        if won:
            efilter = EntityFilter.create('opportunities-opportunities_won', name=_(u"Opportunities won"), model=Opportunity)
            efilter.set_conditions([EntityFilterCondition.build_4_field(model=Opportunity, operator=EntityFilterCondition.EQUALS, name='sales_phase', values=[won.pk])])

            efilter = EntityFilter.create('opportunities-opportunities_lost', name=_(u"Opportunities lost"), model=Opportunity)
            efilter.set_conditions([EntityFilterCondition.build_4_field(model=Opportunity, operator=EntityFilterCondition.EQUALS, name='sales_phase', values=[lost.pk])])

            efilter = EntityFilter.create('opportunities-neither_won_nor_lost_opportunities', name=_(u"Neither won nor lost opportunities"), model=Opportunity)
            efilter.set_conditions([EntityFilterCondition.build_4_field(model=Opportunity, operator=EntityFilterCondition.EQUALS_NOT, name='sales_phase', values=[won.pk, lost.pk])])

        ButtonMenuItem.create_if_needed(pk='opportunities-linked_opp_button',         model=Organisation, button=linked_opportunity_button, order=30)#TODO: This pk is kept for compatibility
        ButtonMenuItem.create_if_needed(pk='opportunities-linked_opp_button_contact', model=Contact,      button=linked_opportunity_button, order=30)

        SearchConfigItem.create_if_needed(Opportunity, ['name', 'made_sales', 'sales_phase__name', 'origin__name'])

        BlockDetailviewLocation.create_4_model_block(order=5, zone=BlockDetailviewLocation.LEFT, model=Opportunity)
        BlockDetailviewLocation.create(block_id=customfields_block.id_,    order=40,  zone=BlockDetailviewLocation.LEFT,  model=Opportunity)
        BlockDetailviewLocation.create(block_id=linked_contacts_block.id_, order=50,  zone=BlockDetailviewLocation.LEFT,  model=Opportunity)
        BlockDetailviewLocation.create(block_id=linked_products_block.id_, order=60,  zone=BlockDetailviewLocation.LEFT,  model=Opportunity)
        BlockDetailviewLocation.create(block_id=linked_services_block.id_, order=62,  zone=BlockDetailviewLocation.LEFT,  model=Opportunity)
        BlockDetailviewLocation.create(block_id=responsibles_block.id_,    order=60,  zone=BlockDetailviewLocation.LEFT,  model=Opportunity)
        BlockDetailviewLocation.create(block_id=quotes_block.id_,          order=70,  zone=BlockDetailviewLocation.LEFT,  model=Opportunity)
        BlockDetailviewLocation.create(block_id=salesorders_block.id_,     order=72,  zone=BlockDetailviewLocation.LEFT,  model=Opportunity)
        BlockDetailviewLocation.create(block_id=invoices_block.id_,        order=74,  zone=BlockDetailviewLocation.LEFT,  model=Opportunity)
        BlockDetailviewLocation.create(block_id=properties_block.id_,      order=450, zone=BlockDetailviewLocation.LEFT,  model=Opportunity)
        BlockDetailviewLocation.create(block_id=relations_block.id_,       order=500, zone=BlockDetailviewLocation.LEFT,  model=Opportunity)
        BlockDetailviewLocation.create(block_id=total_block.id_,           order=2,   zone=BlockDetailviewLocation.RIGHT, model=Opportunity)
        BlockDetailviewLocation.create(block_id=history_block.id_,         order=20,  zone=BlockDetailviewLocation.RIGHT, model=Opportunity)

        if 'activities' in settings.INSTALLED_APPS:
            info('Activities app is installed => we use the "Future activities" & "Past activities" blocks')

            from activities.blocks import future_activities_block, past_activities_block

            BlockDetailviewLocation.create(block_id=future_activities_block.id_, order=20, zone=BlockDetailviewLocation.RIGHT, model=Opportunity)
            BlockDetailviewLocation.create(block_id=past_activities_block.id_,   order=21, zone=BlockDetailviewLocation.RIGHT, model=Opportunity)
            BlockPortalLocation.create(app_name='opportunities', block_id=future_activities_block.id_, order=20)
            BlockPortalLocation.create(app_name='opportunities', block_id=past_activities_block.id_,   order=21)


        if 'assistants' in settings.INSTALLED_APPS:
            info('Assistants app is installed => we use the assistants blocks on detail views and portal')

            from assistants.blocks import alerts_block, memos_block, todos_block, messages_block

            BlockDetailviewLocation.create(block_id=todos_block.id_,    order=100, zone=BlockDetailviewLocation.RIGHT, model=Opportunity)
            BlockDetailviewLocation.create(block_id=memos_block.id_,    order=200, zone=BlockDetailviewLocation.RIGHT, model=Opportunity)
            BlockDetailviewLocation.create(block_id=alerts_block.id_,   order=300, zone=BlockDetailviewLocation.RIGHT, model=Opportunity)
            BlockDetailviewLocation.create(block_id=messages_block.id_, order=500, zone=BlockDetailviewLocation.RIGHT, model=Opportunity)

            BlockPortalLocation.create(app_name='opportunities', block_id=memos_block.id_,    order=100)
            BlockPortalLocation.create(app_name='opportunities', block_id=alerts_block.id_,   order=200)
            BlockPortalLocation.create(app_name='opportunities', block_id=messages_block.id_, order=400)

        if 'emails' in settings.INSTALLED_APPS:
            info('Emails app is installed => we use the emails blocks on detail view')

            from emails.blocks import mails_history_block

            BlockDetailviewLocation.create(block_id=mails_history_block.id_, order=600, zone=BlockDetailviewLocation.RIGHT, model=Opportunity)

        BlockDetailviewLocation.create(block_id=targetting_opps_block.id_, order=16, zone=BlockDetailviewLocation.RIGHT, model=Organisation)

        if 'reports' in settings.INSTALLED_APPS:
            info('Reports app is installed => we create an Opportunity report, with 2 graphs, and related blocks')
            self.create_reports(rt_obj_emit_orga)

    def create_reports(self, rt_obj_emit_orga):
        """Create the report 'Opportunities generated by organisation managed by Creme'"""
        from django.contrib.contenttypes.models import ContentType
        from django.contrib.auth.models import User

        from creme_core.models import EntityFilter, EntityFilterCondition
        from creme_core.models.header_filter import HFI_FIELD, HFI_RELATION
        from creme_core.utils.meta import get_verbose_field_name

        from persons.constants import FILTER_MANAGED_ORGA

        from reports.models import Report, Field, ReportGraph
        from reports.models.graph import RGT_FK, RGT_RANGE

        report_name = _(u"Opportunities generated by a Creme managed organisation")
        opp_ct = ContentType.objects.get_for_model(Opportunity)

        if Report.objects.filter(name=report_name, ct=opp_ct).exists():
            info('It seems that a report "%s" already exists => do not recreate one.')
            return

        #Create a list view filter to use it in the report ---------------------
        try:
            orga_filter = EntityFilter.objects.get(pk=FILTER_MANAGED_ORGA)
        except EntityFilter.DoesNotExist:
            info('Filter "Organisations managed by Creme" does not exists : have you populated the "persons" app ?? [Report can not be created]')
            return

        opp_filter = EntityFilter.create('opportunities-gen_by_managed', _(u"Generated by a Creme managed organisation"), Opportunity)
        opp_filter.set_conditions([EntityFilterCondition.build_4_relation_subfilter(rtype=rt_obj_emit_orga, has=True, subfilter=orga_filter)])

        admin = User.objects.get(pk=1)

        #Create the report -----------------------------------------------------
        opp_report = Report.objects.create(name=report_name, ct=opp_ct, filter=opp_filter, user=admin)
        create_field = Field.objects.create
        opp_report.columns = [create_field(name='name',              title=get_verbose_field_name(Opportunity, 'name'),              order=1, type=HFI_FIELD),
                              create_field(name='estimated_sales',   title=get_verbose_field_name(Opportunity, 'estimated_sales'),   order=2, type=HFI_FIELD),
                              create_field(name='made_sales',        title=get_verbose_field_name(Opportunity, 'made_sales'),        order=3, type=HFI_FIELD),
                              create_field(name='sales_phase__name', title=get_verbose_field_name(Opportunity, 'sales_phase__name'), order=4, type=HFI_FIELD),
                              create_field(name=rt_obj_emit_orga.id, title=unicode(rt_obj_emit_orga),                                order=5, type=HFI_RELATION),
                             ]

        #Create 2 graphs -------------------------------------------------------
        graph_name1 = _(u"Sum %(estimated_sales)s / %(sales_phase)s") % {
                            'estimated_sales': get_verbose_field_name(Opportunity, 'estimated_sales'),
                            'sales_phase':     get_verbose_field_name(Opportunity, 'sales_phase'),
                        }
        graph_name2 = _(u"Sum %(estimated_sales)s / Quarter (90 days on %(closing_date)s)") % {
                            'estimated_sales': get_verbose_field_name(Opportunity, 'estimated_sales'),
                            'closing_date':    get_verbose_field_name(Opportunity, 'closing_date'),
                        }
        create_graph = ReportGraph.objects.create
        rgraph1 = create_graph(name=graph_name1, report=opp_report, abscissa='sales_phase',  ordinate='estimated_sales__sum', type=RGT_FK,    is_count=False, user=admin)
        rgraph2 = create_graph(name=graph_name2, report=opp_report, abscissa='closing_date', ordinate='estimated_sales__sum', type=RGT_RANGE, is_count=False, user=admin, days=90)

        #Create 2 instance block items for the 2 graphs ------------------------
        block_id1 = rgraph1.create_instance_block_config_item().block_id
        block_id2 = rgraph2.create_instance_block_config_item().block_id

        BlockDetailviewLocation.create(block_id=block_id1, order=4, zone=BlockDetailviewLocation.RIGHT, model=Opportunity)
        BlockDetailviewLocation.create(block_id=block_id2, order=6, zone=BlockDetailviewLocation.RIGHT, model=Opportunity)
        BlockPortalLocation.create(app_name='opportunities', block_id=block_id1, order=1)
        BlockPortalLocation.create(app_name='opportunities', block_id=block_id2, order=2)
