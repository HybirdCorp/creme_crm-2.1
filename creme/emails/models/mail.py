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

import logging

from django.db import IntegrityError
from django.db.models import (PositiveIntegerField, PositiveSmallIntegerField, CharField,
        TextField, DateTimeField, ForeignKey, ManyToManyField)
from django.db.transaction import atomic
#from django.db import transaction, IntegrityError
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _, ugettext
from django.template.defaultfilters import removetags

from creme.creme_core.models import CremeModel, CremeEntity

from creme.documents.models import Document

from ..utils import generate_id, EMailSender
from ..constants import MAIL_STATUS_NOTSENT, MAIL_STATUS
from .signature import EmailSignature


logger = logging.getLogger(__name__)
ID_LENGTH = 32


class _Email(CremeModel):
    reads          = PositiveIntegerField(_(u'Number of reads'), blank=True, null=True, default=0)
    status         = PositiveSmallIntegerField(_(u'Status'), default=MAIL_STATUS_NOTSENT)

    sender         = CharField(_(u'Sender'), max_length=100)
    recipient      = CharField(_(u'Recipient'), max_length=100)
    #cc             = CharField(_(u'cc'), max_length=100)
    subject        = CharField(_(u'Subject'), max_length=100, blank=True, null=True)
    #body_html      = TextField()
    body           = TextField(_(u'Body'))
    sending_date   = DateTimeField(_(u"Sending date"), blank=True, null=True)
    reception_date = DateTimeField(_(u"Reception date"), blank=True, null=True)
    #signature      = ForeignKey(EmailSignature, verbose_name=_(u'Signature'), blank=True, null=True) ##merge with body ????
    #attachments    = ManyToManyField(Document, verbose_name=_(u'Attachments'))

    class Meta:
        abstract = True
        app_label = "emails"

    def __unicode__(self):
        return u"Mail<from: %s> <to: %s> <sent: %s> <id: %s>" % (self.sender, self.recipient, self.sending_date, self.id)

    def get_status_str(self):
        return MAIL_STATUS[self.status]

    def get_body(self):
        return self.body



class EntityEmail(_Email, CremeEntity):
    identifier  = CharField(_(u'Email ID'), unique=True, max_length=ID_LENGTH, null=False, blank=False, editable=False, default=generate_id)#TODO: lambda for this
    body_html   = TextField(_(u'Body (HTML)'))
    signature   = ForeignKey(EmailSignature, verbose_name=_(u'Signature'), blank=True, null=True) ##merge with body ????
    attachments = ManyToManyField(Document, verbose_name=_(u'Attachments'))

    creation_label = _('Add an email')

    class Meta:
        app_label = "emails"
        verbose_name = _(u'Email')
        verbose_name_plural = _(u'Emails')
        ordering = ('-sending_date',)

#    @transaction.commit_manually
#    def genid_n_save(self):
#        #BEWARE: manage manually
#        while True:
#            sid = transaction.savepoint()
#
#            try:
#                self.identifier = generate_id()
#                self.save(force_insert=True)
#            except IntegrityError:  #a mail with this id already exists
#                logger.debug('Mail id already exists: %s', self.identifier)
#                self.pk = None
#
#                transaction.savepoint_rollback(sid)
#            else:
#                transaction.savepoint_commit(sid)
#                break
#
#        transaction.commit()
    def genid_n_save(self):
        while True: # TODO: xrange(10000) to avoid infinite loop ??
            self.identifier = generate_id()

            try:
                with atomic():
                    self.save(force_insert=True)
            except IntegrityError:  # A mail with this id already exists
                logger.debug('Mail id already exists: %s', self.identifier)
                self.pk = None
            else:
                return

    def __unicode__(self):
        return ugettext('EMail <from: %(from)s> <to: %(to)s> <status: %(status)s>') % {
                                'from':   self.sender,
                                'to':     self.recipient,
                                'status': self.get_status_str(),
                            }

    def get_absolute_url(self):
        return u"/emails/mail/%s" % self.pk

    @staticmethod
    def get_lv_absolute_url():
        return "/emails/mails"

    @staticmethod
    def create_n_send_mail(sender, recipient, subject, user, body, body_html=u"", signature=None, attachments=None):
        email = EntityEmail(sender=sender,
                            recipient=recipient,
                            subject=subject,
                            body=body,
                            body_html=body_html,
                            signature=signature,
                            user=user,
                           )
        email.genid_n_save()

        if attachments:
            email.attachments = attachments

        email.send()

        return email

    def _pre_save_clone(self, source):
        self.genid_n_save()

    #def get_edit_absolute_url(self):
        #return ""

    def get_body(self):
        if self.body_html:
            return mark_safe(removetags(self.body_html, 'script'))
        else:
            return mark_safe(removetags(self.body.replace('\n', '</br>'), 'script'))

    def send(self):
        sender = EntityEmailSender(body=self.body,
                                   body_html=self.body_html,
                                   signature=self.signature,
                                   attachments=self.attachments.all()
                                  )

        if sender.send(self):
            logger.debug("Mail sent to %s", self.recipient)


class EntityEmailSender(EMailSender):
    def get_subject(self, mail):
        return mail.subject

