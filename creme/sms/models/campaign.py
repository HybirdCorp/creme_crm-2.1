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

from django.db.models import CharField, ManyToManyField
from django.utils.translation import ugettext_lazy as _

from creme_core.models import CremeEntity

from sms.models.messaging_list import MessagingList
from sms.models.recipient import Recipient


class SMSCampaign(CremeEntity):
    name  = CharField(_(u'Name of the campaign'), max_length=100, blank=False, null=False)
    lists = ManyToManyField(MessagingList, verbose_name=_(u'Related messaging lists'))

    class Meta:
        app_label = "sms"
        verbose_name = _(u"SMS campaign")
        verbose_name_plural = _(u"SMS campaigns")

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return "/sms/campaign/%s" % self.id

    def get_edit_absolute_url(self):
        return "/sms/campaign/edit/%s" % self.id

    @staticmethod
    def get_lv_absolute_url():
        return "/sms/campaigns"

    def delete(self):
        self.lists.clear()

        for sending in self.sendings.all():
            sending.delete()

        super(SMSCampaign, self).delete()

    def all_recipients(self):
        mlists = self.lists.all()

        #manual recipients
        #TODO: remove '__id'
        #recipients = list(number for number in Recipient.objects.filter(messaging_list__id__in=(mlist.id for mlist in lists)).values_list('phone', flat=True))
        recipients = list(number for number in Recipient.objects.filter(messaging_list__in=mlists).values_list('phone', flat=True))

        #contacts recipients
        recipients += list(contact.mobile for mlist in mlists for contact in mlist.contacts.all() if contact.mobile)

        return recipients
