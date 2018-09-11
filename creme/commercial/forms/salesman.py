# -*- coding: utf-8 -*-

################################################################################
#    Creme is a free/open-source Customer Relationship Management software
#    Copyright (C) 2009-2018  Hybird
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

import warnings

from creme.creme_core.models import CremeProperty

from creme.persons.forms.contact import ContactForm

from ..constants import PROP_IS_A_SALESMAN


class SalesManCreateForm(ContactForm):
    def __init__(self, *args, **kwargs):
        warnings.warn('commercial.forms.salesman.SalesManCreateForm is deprecated.',
                      DeprecationWarning
                     )
        super().__init__(*args, **kwargs)

    def save(self, *args, **kwargs):
        # instance = super(SalesManCreateForm, self).save(*args, **kwargs)
        instance = super().save(*args, **kwargs)

        CremeProperty.objects.create(type_id=PROP_IS_A_SALESMAN, creme_entity=instance)

        return instance
