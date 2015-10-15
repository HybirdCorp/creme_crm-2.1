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

from math import ceil

from django.forms import ModelChoiceField, IntegerField, CharField
from django.utils.translation import ugettext_lazy as _, ugettext

from creme.creme_core.forms import CremeForm, CremeEntityForm, CremeModelForm
from creme.creme_core.forms.fields import CremeDateTimeField, FilteredEntityTypeField
from creme.creme_core.forms.widgets import Label

from .. import get_act_model, get_pattern_model
from ..models import ActObjective, ActObjectivePatternComponent # Act, ActObjectivePattern


ActObjectivePattern = get_pattern_model()


class ActForm(CremeEntityForm):
    start    = CremeDateTimeField(label=_(u"Start"))
    due_date = CremeDateTimeField(label=_(u"Due date"))

    class Meta(CremeEntityForm.Meta):
#        model = Act
        model = get_act_model()


class ObjectiveForm(CremeModelForm):
    entity_counting = FilteredEntityTypeField(label=_(u'Entity counting'), required=False,
                                              empty_label=_(u'Do not count entity'),
                                             ) # TODO: help text ???

    class Meta:
        model = ActObjective
        #fields = ('name', 'counter_goal')
        fields = '__all__'
        help_texts = {
            'counter_goal': _(u'Integer value the counter has to reach'),
        }

    def __init__(self, entity, *args, **kwargs):
        super(ObjectiveForm, self).__init__(*args, **kwargs)
        self.act = entity

        instance = self.instance
        if instance.pk: # Edition
            fields = self.fields
            efilter = instance.filter

            if efilter and not efilter.can_view(self.user)[0]:
                fields['ec_label'] = CharField(label=fields['entity_counting'].label,
                                               required=False, widget=Label,
                                               initial=_('The filter cannot be changed because it is private.'),
                                              )
                del fields['entity_counting']
            else:
                fields['entity_counting'].initial = instance.ctype_id, instance.filter_id

    def save(self, *args, **kwargs):
        instance = self.instance
        instance.act = self.act
        #instance.ctype, instance.filter = self.cleaned_data['entity_counting']

        ct_n_filter = self.cleaned_data.get('entity_counting')
        if ct_n_filter:
            instance.ctype, instance.filter = ct_n_filter

        return super(ObjectiveForm, self).save(*args, **kwargs)


class ObjectivesFromPatternForm(CremeForm):
    pattern = ModelChoiceField(label=_(u'Pattern'), empty_label=None,
                               queryset=ActObjectivePattern.objects.all()
                              )

    def __init__(self, entity, *args, **kwargs):
        super(ObjectivesFromPatternForm, self).__init__(*args, **kwargs)
        self.act = entity

        self.fields['pattern'].queryset = ActObjectivePattern.objects.filter(segment=entity.segment_id)

    def save(self, *args, **kwargs):
        act = self.act
        pattern = self.cleaned_data['pattern']
        create_objective = ActObjective.objects.create
        won_opps = int(ceil(float(act.expected_sales) / float(pattern.average_sales)))

        create_objective(act=act, name=ugettext(u'Number of won opportunities'), counter_goal=won_opps)

        def create_objectives_from_components(comps, parent_goal):
            for comp in comps:
                counter_goal = int(ceil(parent_goal * (100.0 / comp.success_rate)))
                create_objective(act=act, name=comp.name, counter_goal=counter_goal,
                                 ctype_id=comp.ctype_id, filter_id=comp.filter_id
                                )
                create_objectives_from_components(comp.get_children(), counter_goal)

        create_objectives_from_components(pattern.get_components_tree(), won_opps)


class ObjectivePatternForm(CremeEntityForm):
    class Meta(CremeEntityForm.Meta):
        model = ActObjectivePattern


class _PatternComponentForm(CremeModelForm):
    entity_counting = FilteredEntityTypeField(label=_(u'Entity counting'), required=False,
                                              empty_label=_(u'Do not count entity'),
                                             ) #TODO: help text ???
    success_rate    = IntegerField(label=_(u'Success rate'), min_value=1, max_value=100,
                                   help_text=_(u'Percentage of success')
                                  )

    class Meta:
        model = ActObjectivePatternComponent
        fields = '__all__'

    def save(self, *args, **kwargs):
        instance = self.instance
        instance.ctype, instance.filter = self.cleaned_data['entity_counting']

        return super(_PatternComponentForm, self).save(*args, **kwargs)


class PatternComponentForm(_PatternComponentForm):
    def __init__(self, entity, *args, **kwargs):
        super(PatternComponentForm, self).__init__(*args, **kwargs)
        self.pattern = entity

    def save(self, *args, **kwargs):
        self.instance.pattern = self.pattern
        return super(PatternComponentForm, self).save(*args, **kwargs)


class PatternChildComponentForm(_PatternComponentForm):
    def __init__(self, parent, *args, **kwargs):
        super(PatternChildComponentForm, self).__init__(*args, **kwargs)
        self.parent = parent

    def save(self, *args, **kwargs):
        parent = self.parent
        instance = self.instance

        instance.pattern = parent.pattern
        instance.parent = parent
        return super(PatternChildComponentForm, self).save(*args, **kwargs)


class PatternParentComponentForm(_PatternComponentForm):
    def __init__(self, child, *args, **kwargs):
        super(PatternParentComponentForm, self).__init__(*args, **kwargs)
        self.child = child

    def save(self, *args, **kwargs):
        child = self.child
        instance = self.instance

        instance.pattern = child.pattern
        instance.parent = child.parent
        super(PatternParentComponentForm, self).save(*args, **kwargs)

        child.parent = instance
        child.save() #TODO: use *args/**kwargs ('using' arg)???

        return instance
