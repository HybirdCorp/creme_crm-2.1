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

from datetime import datetime
from logging import debug
from random import choice
from string import ascii_letters, digits
from pickle import dumps, HIGHEST_PROTOCOL

from django.db import IntegrityError
from django.forms import TypedChoiceField, IntegerField
from django.forms.util import ErrorList
from django.template import Template, VariableNode
from django.utils.translation import ugettext_lazy as _

from creme_core.forms import CremeModelForm, CremeEntityField, CremeDateTimeField

from emails.models import EmailTemplate
from emails.models.sending import EmailSending, SENDING_TYPES, SENDING_TYPE_DEFERRED, SENDING_STATE_PLANNED
from emails.models.mail import Email, MAIL_STATUS_NOTSENT, ID_LENGTH


ALLOWED_CHARS = ascii_letters + digits

def generate_id():
    return ''.join(choice(ALLOWED_CHARS) for i in xrange(ID_LENGTH))


class SendingCreateForm(CremeModelForm):
    type         = TypedChoiceField(label=_(u"Type d'envoi"), choices=SENDING_TYPES.iteritems(), coerce=int)
    template     = CremeEntityField(label=_(u'Patron de couriel'), model=EmailTemplate)

    sending_date = CremeDateTimeField(label=_(u"Date d'envoi"), required=False,
                                      help_text=_(u"Obligatoire si l'envoi est différé seulement."))
    hour         = IntegerField(label=_("Heure d'envoi"), required=False, min_value=0, max_value=23)
    minute       = IntegerField(label=_("Minute d'envoi"), required=False, min_value=0, max_value=59)

    blocks = CremeModelForm.blocks.new(('sending_date', _(u"Date de l'envoi"), ['type', 'sending_date', 'hour', 'minute']))

    class Meta:
        model   = EmailSending
        exclude = ('campaign', 'state', 'subject', 'body', 'signature', 'attachments')

    def __init__(self, campaign, *args, **kwargs):
        super(SendingCreateForm, self).__init__(*args, **kwargs)
        self.campaign = campaign

    def clean(self):
        cleaned_data = self.cleaned_data
        sending_date = cleaned_data['sending_date']
        now = datetime.now()

        if cleaned_data['type'] == SENDING_TYPE_DEFERRED:
            if sending_date is None:
                self._errors["sending_date"] = ErrorList([u"Date d'envoi obligatoire pour un envoi différé"])
            elif sending_date < now:
                self._errors["sending_date"] = ErrorList([u"La date d'envoi doit être dans le futur"])
            else:
                cleaned_data['sending_date'] = sending_date.replace(hour=int(cleaned_data.get('hour') or 0),
                                                                    minute=int(cleaned_data.get('minute') or 0))
        else:
            cleaned_data['sending_date'] = now

        return cleaned_data

    def save(self):
        instance = self.instance
        cleaned_data = self.cleaned_data

        instance.campaign = self.campaign
        instance.state = SENDING_STATE_PLANNED

        template = cleaned_data['template']
        instance.subject   = template.subject
        instance.body      = template.body
        instance.signature = template.signature

        super(SendingCreateForm, self).save()

        # M2M need a pk -> after save
        attachments = instance.attachments
        for attachment in template.attachments.all():
            attachments.add(attachment)

        varlist = [varnode.filter_expression.var.var for varnode in Template(template.body).nodelist.get_nodes_by_type(VariableNode)]

        for address, recipient_entity in instance.campaign.all_recipients():
            mail = Email()
            mail.sending = instance
            mail.reads = 0
            mail.status = MAIL_STATUS_NOTSENT
            mail.sender = instance.sender
            mail.recipient = address
            mail.sending_date = instance.sending_date

            if recipient_entity:
                entity = recipient_entity[1]
                mail.recipient_ct = recipient_entity[0]
                mail.recipient_id = entity.id

                context = {}
                for varname in varlist:
                    val = getattr(entity, varname, None)
                    if val:
                        context[varname] = val.encode('utf-8')

                if context:
                    mail.body = dumps(context)
            else:
                mail.recipient_ct = None
                mail.recipient_id = None

            #BEWARE: manage manually 
            while True:
                try:
                    mail.id = generate_id()
                    mail.save(force_insert=True)
                except IntegrityError:  #a mail with this id already exists
                    debug('Mail id already exists: %s', mail.id)
                    mail.pk = None
                else:
                    break
