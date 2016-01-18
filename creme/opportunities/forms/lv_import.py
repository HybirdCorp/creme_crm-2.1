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

from django.forms import ModelChoiceField
from django.utils.translation import ugettext as _

from creme.creme_core.forms.list_view_import import (ImportForm4CremeEntity,
        EntityExtractorField)

from creme.persons import get_contact_model, get_organisation_model

Organisation = get_organisation_model()
Contact = get_contact_model()


def get_csv_form_builder(header_dict, choices):
    class OpportunityCSVImportForm(ImportForm4CremeEntity):
        target = EntityExtractorField([(Organisation, 'name'), (Contact, 'last_name')],
                                      choices, label=_('Target')
                                     )
        emitter = ModelChoiceField(label=_(u"Concerned organisation"), empty_label=None,
                                   queryset=Organisation.get_all_managed_by_creme(),
                                  )

        def _pre_instance_save(self, instance, line):
            cdata = self.cleaned_data

            if not instance.pk:  # Creation
                instance.emitter = cdata['emitter']

            target, err_msg = cdata['target'].extract_value(line, self.user)
            instance.target = target
            self.append_error(line, err_msg, instance)  # Error is really appended if 'err_msg' is not empty


    return OpportunityCSVImportForm
