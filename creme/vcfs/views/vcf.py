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

from django.http import HttpResponse, Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.encoding import smart_str
from django.utils.translation import ugettext_lazy as _

from creme.creme_core.auth.decorators import permission_required, login_required
from creme.creme_core.utils import get_from_POST_or_404

from creme.persons.models import Contact

from ..forms.vcf import VcfForm, VcfImportForm
from ..vcfgenerator import VcfGenerator


@login_required
@permission_required(('persons', 'persons.add_contact'))
def vcf_import(request):
    user = request.user
    submit_label = _('Save the contact')

    if request.method == 'POST':
        POST = request.POST

        #try:
            #step = int(POST.get('vcf_step', 0))
        #except ValueError:
            #raise Http404('"vcf_step" must be in {0, 1}')
        step = get_from_POST_or_404(POST, 'vcf_step', cast=int, default=0)

        form = VcfForm(user=user, data=POST, files=request.FILES)

        if step == 0:
            if form.is_valid():
                form = VcfImportForm(user=user,
                                     vcf_data=form.cleaned_data['vcf_file'],
                                     initial={'vcf_step': 1},
                                    )
            else:
                submit_label = _('Import this VCF file')
        else:
            if step != 1:
                raise Http404('"vcf_step" must be in {0, 1}')

            form = VcfImportForm(user=user, data=POST)

            if form.is_valid():
                contact = form.save()
                return redirect(contact)

        cancel_url = POST.get('cancel_url')
    else:
        form = VcfForm(user=user, initial={'vcf_step': 0})
        submit_label = _('Import this VCF file')
        cancel_url = request.META.get('HTTP_REFERER')

    return render(request, 'creme_core/generics/blockform/edit.html',
                  {'form':         form,
                   'title':        _('Import contact from VCF file'),
                   'submit_label': submit_label,
                   'cancel_url':   cancel_url,
                  }
                 )

@login_required
@permission_required('persons')
def vcf_export(request, contact_id):
    person = get_object_or_404(Contact, pk=contact_id)
    request.user.has_perm_to_view_or_die(person)

    vc = VcfGenerator(person).serialize()

    response = HttpResponse(vc, content_type='text/vcard')
    response['Content-Disposition'] = 'attachment; filename="%s.vcf"' % smart_str(person.last_name)

    return response
