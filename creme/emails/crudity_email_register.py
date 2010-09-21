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

from creme.crudity.models.history import History
import os
from itertools import chain

from django.utils.translation import ugettext
from django.utils.translation import ugettext as _

from creme_core.views.file_handling import handle_uploaded_file
from creme_core.models.relation import Relation

from creme_settings import EMAILS_ENTITYEMAIL_FROM_EMAIL

from crudity import CREATE
from crudity.backends.email import CreateFromEmailBackend

from documents.models.document import Document
from documents.models.folder import Folder
from documents.models.other_models import FolderCategory
from documents.constants import REL_OBJ_RELATED_2_DOC

from emails.models.mail import EntityEmail, MAIL_STATUS_SYNCHRONIZED_WAITING
from emails.blocks import WaitingSynchronizationMailsBlock, SpamSynchronizationMailsBlock

create_email_settings = EMAILS_ENTITYEMAIL_FROM_EMAIL.get(CREATE)

CREATE_ENTITYEMAIL_LIMIT_FROMS = create_email_settings.get("limit_froms")
CREATE_ENTITYEMAIL_IN_SANDBOX  = create_email_settings.get("in_sandbox", True)
CREATE_ENTITYEMAIL_BODY_MAP    = create_email_settings.get("body_map", {})

class CreateEntityEmailFromEmail(CreateFromEmailBackend):
    """This backend is implemented as the default backend so there are no
    password or subject verification
    """
    password        = None
    limit_froms     = CREATE_ENTITYEMAIL_LIMIT_FROMS
    in_sandbox      = CREATE_ENTITYEMAIL_IN_SANDBOX
    body_map        = CREATE_ENTITYEMAIL_BODY_MAP
    model           = EntityEmail
    subject         = None
    attachment_path = ['upload','emails','attachments']
    blocks          = (WaitingSynchronizationMailsBlock, SpamSynchronizationMailsBlock)

    def __init__(self):
        super(CreateEntityEmailFromEmail, self).__init__()

    def create(self, email, current_user):

        if not self.authorize_senders(email.senders):
            return

        current_user_id = current_user.id
        #TODO: create category in the populate ?? refactor
        folder_cat, is_cat_created  = FolderCategory.objects.get_or_create(name=u"Fichiers reçus par mail") #TODO: i18n

        folder, is_fold_created = Folder.objects.get_or_create(title=u'Fichiers de %s reçus par mail' % current_user.username, #TODO: i18n
                                                               user=current_user,
                                                               category=folder_cat)

        mail = EntityEmail()
        mail.status = MAIL_STATUS_SYNCHRONIZED_WAITING

        mail.body      = email.body.encode('utf-8')
        mail.body_html = email.body_html.encode('utf-8')
        mail.sender    = u', '.join(set(email.senders))
        mail.recipient = u', '.join(set(chain(email.tos, email.ccs)))
        mail.subject   = email.subject
        mail.user_id   = current_user_id
        if email.dates:
            mail.reception_date = email.dates[0]
        mail.genid_n_save()

        attachment_path = self.attachment_path

        for attachment in email.attachments:
            filename, file = attachment
            path = handle_uploaded_file(file, path=attachment_path, name=filename)
            doc = Document()
            doc.title = u"%s (mail %s)" % (path.rpartition(os.sep)[2], mail.id)
            doc.description = ugettext(u"Received with the mail %s") % (mail, )
            doc.filedata = path
            doc.user_id = current_user_id
            doc.folder = folder
            doc.save()
            Relation.create(doc, REL_OBJ_RELATED_2_DOC, mail)

        history = History()
        history.entity = mail
        history.type = self.type
        history.description = _(u"Creation of %(entity)s") % {'entity': mail}
        history.save()


crud_register = {
    CREATE: [
        ("*", CreateEntityEmailFromEmail()),
    ],
}