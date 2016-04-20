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

# from future_builtins import filter

from django.core.urlresolvers import reverse
from django.db.models import (ForeignKey, CharField, TextField, PositiveIntegerField,
        BooleanField, DateField, EmailField, URLField, SET_NULL)
from django.utils.translation import ugettext_lazy as _

from creme.creme_core.constants import PROP_IS_MANAGED_BY_CREME
from creme.creme_core.models import CremeEntity
from creme.creme_core.models.fields import PhoneField

from creme.media_managers.models import Image

from .. import get_contact_model, get_organisation_model
from ..constants import REL_SUB_EMPLOYED_BY, REL_SUB_MANAGES

from .base import PersonWithAddressesMixin
from .other_models import StaffSize, LegalForm, Sector


class AbstractOrganisation(CremeEntity, PersonWithAddressesMixin):
    name = CharField(_(u'Name'), max_length=200)

    description = TextField(_(u'Description'), blank=True).set_tags(optional=True)

    phone    = PhoneField(_(u'Phone number'), max_length=100, blank=True).set_tags(optional=True)
    fax      = CharField(_(u'Fax'), max_length=100, blank=True).set_tags(optional=True)
    email    = EmailField(_(u'Email address'), blank=True).set_tags(optional=True)
    url_site = URLField(_(u'Web Site'), max_length=500, blank=True).set_tags(optional=True)

    sector     = ForeignKey(Sector, verbose_name=_(u'Sector'),
                            blank=True, null=True, on_delete=SET_NULL,
                           ).set_tags(optional=True)
    legal_form = ForeignKey(LegalForm, verbose_name=_(u'Legal form'),
                            blank=True, null=True, on_delete=SET_NULL,
                           ).set_tags(optional=True)
    staff_size = ForeignKey(StaffSize, verbose_name=_(u'Staff size'),
                            blank=True, null=True, on_delete=SET_NULL,
                           ).set_tags(optional=True)

    capital        = PositiveIntegerField(_(u'Capital'), blank=True, null=True)\
                                         .set_tags(optional=True)
    annual_revenue = CharField(_(u'Annual revenue'), max_length=100, blank=True)\
                              .set_tags(optional=True)

    siren = CharField(_(u'SIREN'), max_length=100, blank=True).set_tags(optional=True)
    naf   = CharField(_(u'NAF code'), max_length=100 , blank=True).set_tags(optional=True)
    siret = CharField(_(u'SIRET'), max_length=100, blank=True).set_tags(optional=True)
    rcs   = CharField(_(u'RCS/RM'), max_length=100, blank=True).set_tags(optional=True)

    tvaintra       = CharField(_(u'VAT number'), max_length=100, blank=True)\
                              .set_tags(optional=True)
    subject_to_vat = BooleanField(_(u'Subject to VAT'), default=True).set_tags(optional=True)

    creation_date = DateField(_(u'Date of creation of the organisation'),
                              blank=True, null=True,
                             ).set_tags(optional=True)
    image         = ForeignKey(Image, verbose_name=_(u'Logo'), blank=True, null=True, on_delete=SET_NULL)\
                              .set_tags(optional=True)

    # Needed because we expand it's function fields in other apps (ie. billing)
    # TODO: refactor
    function_fields = CremeEntity.function_fields.new()

    creation_label = _('Add an organisation')

    class Meta:
        abstract = True
        app_label = "persons"
        ordering = ('name',)
        verbose_name = _(u'Organisation')
        verbose_name_plural = _(u'Organisations')
        index_together = ('name', 'cremeentity_ptr')

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('persons__view_organisation', args=(self.id,))

    @staticmethod
    def get_create_absolute_url():
        return reverse('persons__create_organisation')

    def get_edit_absolute_url(self):
        return reverse('persons__edit_organisation', args=(self.id,))

    @staticmethod
    def get_lv_absolute_url():
        """URL for list_view """
        return reverse('persons__list_organisations')

    # TODO: move in a manager ??
    def get_managers(self):
        return get_contact_model().objects\
                                  .filter(is_deleted=False,
                                          relations__type=REL_SUB_MANAGES,
                                          relations__object_entity=self.id,
                                         )

    # TODO: move in a manager ??
    def get_employees(self):
        return get_contact_model().objects\
                                  .filter(is_deleted=False,
                                          relations__type=REL_SUB_EMPLOYED_BY,
                                          relations__object_entity=self.id,
                                         )

    # TODO: move in a manager ??
    @staticmethod
    def get_all_managed_by_creme():
        return get_organisation_model().objects\
                                       .filter(is_deleted=False,
                                               properties__type=PROP_IS_MANAGED_BY_CREME,
                                              )

    def _post_save_clone(self, source):
        self._aux_post_save_clone(source)


class Organisation(AbstractOrganisation):
    class Meta(AbstractOrganisation.Meta):
        swappable = 'PERSONS_ORGANISATION_MODEL'
