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

from django.db.models import CharField, BooleanField, TextField
from django.utils.translation import ugettext_lazy as _

from creme_core.models import CremeModel

class SettlementTerms(CremeModel):
    name = CharField(_(u'Settlement terms'), max_length=100)

    def __unicode__(self):
        return self.name

    class Meta:
        app_label = 'billing'
        verbose_name = _(u'Settlement terms')
        verbose_name_plural = _(u'Settlement terms')





#TODO: use a base abstract class ??

class InvoiceStatus(CremeModel):
    name      = CharField(_(u'Status'), max_length=100)
    is_custom = BooleanField(default=True) #used by creme_config

    def __unicode__(self):
        return self.name

    class Meta:
        app_label = 'billing'
        verbose_name = _(u'Invoice status')
        verbose_name_plural = _(u'Invoice status')


class QuoteStatus(CremeModel):
    name      = CharField(_(u'Status'), max_length=100)
    is_custom = BooleanField(default=True) #used by creme_config

    def __unicode__(self):
        return self.name

    class Meta:
        app_label = 'billing'
        verbose_name = _(u'Quote status')
        verbose_name_plural = _(u'Quote status')


class SalesOrderStatus(CremeModel):
    name      = CharField(_(u'Status'), max_length=100)
    is_custom = BooleanField(default=True) #used by creme_config

    def __unicode__(self):
        return self.name

    class Meta:
        app_label = 'billing'
        verbose_name = _(u'Sales order status')
        verbose_name_plural = _(u'Sales order status')


class CreditNoteStatus(CremeModel):
    name      = CharField(_(u'Status'), max_length=100)
    is_custom = BooleanField(default=True) #used by creme_config

    def __unicode__(self):
        return self.name

    class Meta:
        app_label = 'billing'
        verbose_name = _(u"Credit note status")
        verbose_name_plural = _(u"Credit note status")

class AdditionalInformation(CremeModel):
    name        = CharField(_(u'Name'), max_length=100)
    description = TextField(verbose_name=_(u"Description"), blank=True, null=True)
    is_custom   = BooleanField(default=True) #used by creme_config

    def __unicode__(self):
        return self.name

    class Meta:
        app_label = 'billing'
        verbose_name = _(u"Additional information")
        verbose_name_plural = _(u"Additional information")


class PaymentTerms(CremeModel):
    name        = CharField(_(u'Payment terms'), max_length=100)
    description = TextField(verbose_name=_(u"Description"), blank=True, null=True)
    is_custom   = BooleanField(default=True) #used by creme_config
    
    def __unicode__(self):
        return self.name

    class Meta:
        app_label = 'billing'
        verbose_name = _(u'Payment terms')
        verbose_name_plural = _(u'Payments terms')