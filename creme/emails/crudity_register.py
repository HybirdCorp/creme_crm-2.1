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

import os
from itertools import chain

from django.utils.translation import ugettext as _

from creme.creme_core.models import Relation
from creme.creme_core.views.file_handling import handle_uploaded_file

from creme.documents.constants import (REL_OBJ_RELATED_2_DOC,
        DOCUMENTS_FROM_EMAILS, DOCUMENTS_FROM_EMAILS_NAME)
from creme.documents.models import Document, Folder, FolderCategory

from creme.crudity.backends.models import CrudityBackend
from creme.crudity.inputs.base import CrudityInput
from creme.crudity.inputs.email import CreateEmailInput
from creme.crudity.models import History

from .blocks import WaitingSynchronizationMailsBlock, SpamSynchronizationMailsBlock
from .models import EntityEmail
from .constants import MAIL_STATUS_SYNCHRONIZED_WAITING


class EntityEmailBackend(CrudityBackend):
    model           = EntityEmail
    blocks          = (WaitingSynchronizationMailsBlock, SpamSynchronizationMailsBlock)
    attachment_path = ['upload', 'emails', 'attachments']

    def fetcher_fallback(self, email, current_user, *args, **kwargs):
        if not CrudityInput().authorize_senders(self, email.senders):
            return

        if self.is_sandbox_by_user:
            #current_user = self.get_owner(sender=email.senders[0])
            current_user = CreateEmailInput.get_owner(True, sender=email.senders[0])

        current_user_id = current_user.id
        cat_name = unicode(DOCUMENTS_FROM_EMAILS_NAME)

        try:
            folder_cat = FolderCategory.objects.get(name=cat_name)
        except FolderCategory.DoesNotExist:
            try:
                folder_cat = FolderCategory.objects.get(pk=DOCUMENTS_FROM_EMAILS)
            except FolderCategory.DoesNotExist:
                folder_cat = FolderCategory.objects.create(pk=DOCUMENTS_FROM_EMAILS,
                                                           name=cat_name,
                                                          )

        folder = Folder.objects.get_or_create(title=_(u"%(username)s's files received by email") % {
                                                            'username': current_user.username,
                                                        },
                                              defaults={'user': current_user,
                                                        'category': folder_cat,
                                                       }
                                             )[0]

        mail = EntityEmail(status=MAIL_STATUS_SYNCHRONIZED_WAITING,
                           body=email.body.encode('utf-8'),
                           body_html=email.body_html.encode('utf-8'),
                           sender=u', '.join(set(email.senders)),
                           recipient=u', '.join(set(chain(email.tos, email.ccs))),
                           subject=email.subject,
                           user_id=current_user_id,
                          )
        if email.dates:
            mail.reception_date = email.dates[0]
        mail.genid_n_save()

        attachment_path = self.attachment_path
        create_relation = Relation.objects.create

        doc_description = _(u"Received with the mail %s") % (mail, )

        for attachment in email.attachments:
            filename, file = attachment
            path = handle_uploaded_file(file, path=attachment_path, name=filename)
            doc = Document.objects.create(title=u"%s (mail %s)" % (path.rpartition(os.sep)[2], mail.id),
                                          description=doc_description,
                                          filedata=path,
                                          user_id=current_user_id,
                                          folder=folder,
                                         )

            create_relation(subject_entity=doc, type_id=REL_OBJ_RELATED_2_DOC,
                            object_entity=mail, user_id=current_user_id
                           )

        History.objects.create(entity=mail,
                               action="create",
                               source="email - raw",
                               description=_(u"Creation of %(entity)s") % {'entity': mail},
                               user=current_user,
                              )

backends = [EntityEmailBackend, ]
