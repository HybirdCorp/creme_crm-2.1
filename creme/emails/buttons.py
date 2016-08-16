# -*- coding: utf-8 -*-

################################################################################
#    Creme is a free/open-source Customer Relationship Management software
#    Copyright (C) 2009-2016  Hybird
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

from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _

from creme.creme_core.auth import build_link_perm as lperm
from creme.creme_core.gui.button_menu import Button

from . import get_entityemail_model
from .constants import REL_SUB_MAIL_RECEIVED, REL_SUB_MAIL_SENDED, REL_SUB_RELATED_TO
#from .models import EntityEmail


EntityEmail = get_entityemail_model()
# entity_email_ct = ContentType.objects.get_for_model(EntityEmail)


class EntityEmailLinkButton(Button):
    id_           = Button.generate_id('emails', 'entity_email_link')
    verbose_name  = _(u'Link this email to')
    template_name = 'emails/templatetags/button_entityemail_link.html'
    permission    = lperm(EntityEmail)

    def get_ctypes(self):
        return (EntityEmail, )

    def render(self, context):
        # context['entity_email_ct_id'] = entity_email_ct.id
        context['entity_email_ct_id'] = ContentType.objects.get_for_model(EntityEmail).id
        context['rtypes'] = ','.join([REL_SUB_MAIL_SENDED, REL_SUB_MAIL_RECEIVED, REL_SUB_RELATED_TO])

        return super(EntityEmailLinkButton, self).render(context)


entityemail_link_button = EntityEmailLinkButton()
