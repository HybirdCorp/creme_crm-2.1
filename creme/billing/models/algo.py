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

from django.apps import apps
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db.models import Model, CharField, ForeignKey, IntegerField
from django.utils.translation import ugettext_lazy as _

from creme.creme_core.models import CremeModel
from creme.creme_core.models.fields import CTypeForeignKey

from creme.persons import get_organisation_model
#from creme.persons.models import Organisation


class ConfigBillingAlgo(CremeModel):
#    organisation = ForeignKey(Organisation, verbose_name=_(u'Organisation'))
    organisation = ForeignKey(settings.PERSONS_ORGANISATION_MODEL, verbose_name=_(u'Organisation'))
    name_algo    = CharField(_(u"Algo name"), max_length=400)
    #ct           = ForeignKey(ContentType)
    ct           = CTypeForeignKey()

    class Meta:
        app_label = 'billing'


class SimpleBillingAlgo(Model):
#    organisation = ForeignKey(Organisation, verbose_name=_(u'Organisation'))
    organisation = ForeignKey(settings.PERSONS_ORGANISATION_MODEL, verbose_name=_(u'Organisation'))
    last_number  = IntegerField()
    prefix       = CharField(_(u'Invoice prefix'), max_length=400)
    #ct           = ForeignKey(ContentType)
    ct           = CTypeForeignKey()

    ALGO_NAME = "SIMPLE_ALGO"

    class Meta:
        app_label = 'billing'
        unique_together = ("organisation", "last_number", "ct")


#TODO; use AppConfig.ready() ??
if apps.is_installed('creme.billing'): #useful for tests (this file could be loaded even if the app is not installed)
    from django.db.models.signals import post_save
    from django.dispatch import receiver

    from creme.creme_core.constants import PROP_IS_MANAGED_BY_CREME
    from creme.creme_core.models import CremeProperty

    @receiver(post_save, sender=CremeProperty)
    def _simple_conf_billing_for_org_managed_by_creme(sender, instance, created, **kwargs):
        if not created:
            return

        from .quote import Quote
        from .sales_order import SalesOrder
        from .invoice import Invoice

        get_ct = ContentType.objects.get_for_model

        if instance.type_id == PROP_IS_MANAGED_BY_CREME and \
           instance.creme_entity.entity_type_id == get_ct(get_organisation_model()).id:
            orga = instance.creme_entity.get_real_entity()

            if not ConfigBillingAlgo.objects.filter(organisation=orga):
                for model, prefix in [(Quote,      settings.QUOTE_NUMBER_PREFIX),
                                      (Invoice,    settings.INVOICE_NUMBER_PREFIX),
                                      (SalesOrder, settings.SALESORDER_NUMBER_PREFIX)]:
                    ct = get_ct(model)
                    ConfigBillingAlgo.objects.create(organisation=orga, name_algo=SimpleBillingAlgo.ALGO_NAME, ct=ct)
                    SimpleBillingAlgo.objects.create(organisation=orga, last_number=0, prefix=prefix, ct=ct)
