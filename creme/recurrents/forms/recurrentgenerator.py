# -*- coding: utf-8 -*-

################################################################################
#    Creme is a free/open-source Customer Relationship Management software
#    Copyright (C) 2009-2014  Hybird
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

from django.forms import DateTimeField
#from django.shortcuts import redirect
from django.utils.translation import ugettext_lazy as _
#from django.contrib.formtools.wizard import FormWizard

from creme.creme_core.forms import CremeEntityForm
from creme.creme_core.forms.fields import EntityCTypeChoiceField
from creme.creme_core.forms.widgets import DateTimeWidget

from ..models import RecurrentGenerator
from ..registry import recurrent_registry


class RecurrentGeneratorEditForm(CremeEntityForm):
    first_generation = DateTimeField(label=_(u'Date of the first generation'),
                                     widget=DateTimeWidget(),
                                    )

    class Meta(CremeEntityForm.Meta):
        model = RecurrentGenerator


class RecurrentGeneratorCreateForm(RecurrentGeneratorEditForm):
    ct = EntityCTypeChoiceField(label=_(u'Type of resource used as template'))

    def __init__(self, *args, **kwargs):
        #kwargs['user'] = kwargs['initial']['user']
        #super(RecurrentGeneratorCreateForm, self).__init__(data=args[0], **kwargs)
        super(RecurrentGeneratorCreateForm, self).__init__(*args, **kwargs)

        has_perm = self.user.has_perm_to_create
        self.fields['ct'].ctypes = [ctype for ctype in recurrent_registry.ctypes
                                            if has_perm(ctype.model_class())
                                   ]

    def save(self):
        instance = self.instance
        instance.last_generation = instance.first_generation #TODO: in model.save() ??
        instance.ct = self.cleaned_data['ct']

        return super(RecurrentGeneratorCreateForm, self).save()


#TODO: remove the 2 useless templates files
##todo: it there  a problem: we create _one_ instance of RecurrentGeneratorWizard (so attributes are 'global'),
##      and we set the form_list[1] to different values ??? (Django wizrd modify self.step itself...)
#class RecurrentGeneratorWizard(FormWizard):
    #def __init__(self):
        ## The second form of the wizard is set to None because it will be determined at execution
        #super(RecurrentGeneratorWizard, self).__init__([RecurrentGeneratorCreateForm, None])

    #def done(self, request, form_list):
        ## We save in db the generator with his linked ressource
        #generator_form = self.get_form(0, request.POST) # form corresponding to generator metadata
        #resource_form  = self.get_form(1, request.POST) # form corresponding to the clonable resource

        #if resource_form.is_valid():
            #resource_form.save()
            #generator_form.instance.template = resource_form.instance

        #if generator_form.is_valid():
            #generator_form.save()

        #return redirect(resource_form.instance)

    #def process_step(self, request, form, step):
        #if step == 0 and form.is_valid():
            #base_class = recurrent_registry.get_form_of_template(form.cleaned_data['ct'])

            #class _TemplateClass(base_class):
                #def __init__(self, *args, **kwargs):
                    #kwargs['user'] = kwargs['initial']['user']
                    #base_class.__init__(self, data=args[0], **kwargs)

            #self.form_list[1] = _TemplateClass

    #def parse_params(self, request, *args, **kwargs):
        #self.initial[0] = {'user': request.user}
        #self.initial[1] = {'user': request.user}

        #if request.method == 'POST':
            #form = self.get_form(0, request.POST)

            #if form.is_valid():
                #self.initial[1].update(ct=form.cleaned_data['ct'].id)

    #def get_template(self, step):
        #return 'recurrents/wizard_generator.html'
