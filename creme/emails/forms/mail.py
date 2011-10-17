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

from itertools import chain

from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.forms.fields import EmailField, BooleanField, CharField
from django.forms.util import ErrorList
from django.utils.translation import ugettext_lazy as _, ugettext

from creme_core.models.relation import Relation
from creme_core.forms.fields import MultiCremeEntityField, CremeEntityField
from creme_core.forms.base import CremeEntityForm, FieldBlockManager
from creme_core.forms.widgets import TinyMCEEditor

from documents.models import Document

from persons.models import Contact, Organisation

from emails.models import EntityEmail
from emails.constants import REL_SUB_MAIL_RECEIVED, REL_SUB_MAIL_SENDED


invalid_email_error = _(u'The email address for %(entity)s is invalid')

class EntityEmailForm(CremeEntityForm):
    """Mails are related to the selected contacts/organisations & the 'current' entity.
    Mails are send to selected contacts/organisations.
    """
    sender       = EmailField(label=_(u'Sender'))

    #TODO: use the new GenericEntityField ?? When it manages q_filter
    c_recipients = MultiCremeEntityField(label=_(u'Contacts'),      required=False, model=Contact,      q_filter={'email__isnull': False})
    o_recipients = MultiCremeEntityField(label=_(u'Organisations'), required=False, model=Organisation, q_filter={'email__isnull': False})

#    body_html    = CharField(label=_(u'Body'), widget=TinyMCEEditor())

    attachments  = MultiCremeEntityField(label=_(u'Attachments'), required=False, model=Document)
    send_me      = BooleanField(label=_(u'Send me a copy of this mail'), required=False)

    blocks = FieldBlockManager(
            ('recipients', _(u'Who'),  ['user', 'sender', 'send_me', 'c_recipients', 'o_recipients']),
            ('content',    _(u'What'), ['subject', 'body', 'body_html']),
            ('extra',      _(u'With'), ['signature', 'attachments']),
        )

    class Meta:
        model  = EntityEmail
        fields = ('sender', 'subject', 'body', 'body_html', 'signature')#, 'attachments')

    def __init__(self, entity, *args, **kwargs):
        super(EntityEmailForm, self).__init__(*args, **kwargs)
        self.entity = entity

        if isinstance(entity, Organisation):
            self.fields['o_recipients'].initial = [entity.pk]
        elif isinstance(entity, Contact):
            self.fields['c_recipients'].initial = [entity.pk]

        self.user_contact = contact = Contact.objects.get(is_user=self.user)

        if contact.email:
            self.fields['sender'].initial = contact.email

    def validate_entity_email(self, field_name, entities):
        recipients_errors = []
        for entity in entities:
            try:
                validate_email(entity.email)
            except Exception, e:#Better exception ?
                recipients_errors.append(invalid_email_error % {'entity': entity})

        if recipients_errors:
            self.errors[field_name] = ErrorList(recipients_errors)

    def clean(self):
        cleaned_data = self.cleaned_data

        contacts      = list(cleaned_data.get('c_recipients', []))
        organisations = list(cleaned_data.get('o_recipients', []))

        if not contacts and not organisations:
            raise ValidationError(ugettext(u'Select at least a Contact or an Organisation'))

        #TODO: Join this 2 lines when using GenericEntityField
        self.validate_entity_email('c_recipients', contacts)
        self.validate_entity_email('o_recipients', organisations)

        return cleaned_data

    def save(self):
        get_data = self.cleaned_data.get

        sender      = get_data('sender')
        subject     = get_data('subject')
        body        = get_data('body')
        body_html   = get_data('body_html')
        signature   = get_data('signature')
        attachments = get_data('attachments')
        user        = get_data('user')

        if get_data('send_me'):
            EntityEmail.create_n_send_mail(sender, sender, subject, user, body, body_html, signature, attachments)

        user_contact = self.user_contact
        create_relation = Relation.objects.create

        for recipient in chain(get_data('c_recipients', []), get_data('o_recipients', [])):
            email = EntityEmail.create_n_send_mail(sender, recipient.email, subject, user, body, body_html, signature, attachments)

            create_relation(subject_entity=email, type_id=REL_SUB_MAIL_SENDED,   object_entity=user_contact, user=user)
            create_relation(subject_entity=email, type_id=REL_SUB_MAIL_RECEIVED, object_entity=recipient,    user=user)
