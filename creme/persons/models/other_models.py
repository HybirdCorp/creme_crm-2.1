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

from django.db.models import Model, CharField, TextField, ManyToManyField
from django.utils.translation import ugettext_lazy as _

from creme_core.models import CremeModel

from media_managers.models import Image


__all__ = ('Civility', 'Position', 'StaffSize', 'LegalForm', 'Sector', 'MailSignature')

class Civility(CremeModel):
    title = CharField(_(u'Title'), max_length=100)

    def __unicode__(self):
        return self.title

    class Meta:
        app_label = "persons"
        verbose_name = _(u'Civility')
        verbose_name_plural = _(u'Civilities')


class Position(CremeModel):
    title = CharField(_(u'Title'), max_length=100)

    def __unicode__(self):
        return self.title

    class Meta:
        app_label = "persons"
        verbose_name = _(u'People position')
        verbose_name_plural = _(u'People positions')


class Sector(CremeModel):
    title = CharField(_(u'Title'), max_length=100)

    def __unicode__(self):
        return self.title

    class Meta:
        app_label = "persons"
        verbose_name = _(u"Line of business")
        verbose_name_plural = _(u"Lines of business")


class LegalForm(CremeModel):
    title = CharField(_(u'Title'), max_length=100)

    def __unicode__(self):
        return self.title

    class Meta:
        app_label = "persons"
        verbose_name = _(u'Legal form')
        verbose_name_plural = _(u'Legal forms')


class StaffSize(CremeModel):
    size = CharField(_(u'Size'), max_length=100)

    def __unicode__(self):
        return self.size

    class Meta:
        app_label = "persons"
        verbose_name = _(u"Organisation staff size")
        verbose_name_plural = _(u"Organisation staff sizes")


class MailSignature(CremeModel):
    sign_name = CharField(_(u'Signature name'), max_length=100)
    corpse    = TextField(_(u'Body'))
    images    = ManyToManyField(Image, verbose_name=_(u'Images'),
                           help_text=_(u'Images embedded in emails (but not as attached).'),
                           blank=True, null=True, related_name='MailSignatureImages_set')

    def __unicode__(self):
        return self.sign_name

    class Meta:
        app_label = "persons"
        verbose_name = _(u"Email signature")
        verbose_name_plural = _(u"Email signatures")
        ordering = ('sign_name',)
