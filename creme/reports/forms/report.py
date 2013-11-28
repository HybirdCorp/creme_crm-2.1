# -*- coding: utf-8 -*-

################################################################################
#    Creme is a free/open-source Customer Relationship Management software
#    Copyright (C) 2009-2013  Hybird
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

from collections import defaultdict
from functools import partial
from itertools import chain, count
#import logging

#from django.db.models.query_utils import Q
from django.db.transaction import commit_on_success
from django.forms.fields import MultipleChoiceField, ChoiceField
from django.forms.util import ErrorList #ValidationError
from django.utils.datastructures import SortedDict as OrderedDict #use python2.7 OrderedDict later.....
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _, ugettext
from django.contrib.contenttypes.models import ContentType

from creme.creme_core.core.entity_cell import (EntityCellRegularField,
        EntityCellCustomField, EntityCellFunctionField, EntityCellRelation)
from creme.creme_core.forms import CremeEntityForm, CremeForm
from creme.creme_core.forms.widgets import OrderedMultipleChoiceWidget
from creme.creme_core.forms.fields import AjaxModelChoiceField, CreatorEntityField, DateRangeField #AjaxMultipleChoiceField
from creme.creme_core.models import HeaderFilter, EntityFilter, RelationType, CustomField
from creme.creme_core.registry import export_backend_registry
from creme.creme_core.utils.meta import get_date_fields, ModelFieldEnumerator

from ..constants import RFT_FIELD, RFT_RELATION, RFT_CUSTOM, RFT_FUNCTION, RFT_CALCULATED, RFT_RELATED
from ..utils import encode_datetime
from ..models import Report, Field
from ..report_aggregation_registry import field_aggregation_registry


#logger = logging.getLogger(__name__)


_CFIELD_PREFIX = 'cf__'

def get_aggregate_custom_fields(model, aggregate_pattern): #TODO: move to utils ?? as protected method ??
    for cf in CustomField.objects.filter(content_type=ContentType.objects.get_for_model(model),
                                         #field_type__in=[CustomField.INT, CustomField.FLOAT]
                                         field_type__in=field_aggregation_registry.authorized_customfields,
                                        ):
        yield ('%s%s__%s' % (_CFIELD_PREFIX, cf.field_type, aggregate_pattern % cf.id),
               cf.name
              )


class CreateForm(CremeEntityForm):
    hf     = AjaxModelChoiceField(label=_(u"Existing view"), queryset=HeaderFilter.objects.none(), #required=True,
                                  help_text=_('The columns of the report will be copied from the list view.')
                                 )
    filter = AjaxModelChoiceField(label=_(u"Filter"), queryset=EntityFilter.objects.none(), required=False)

    #regular_fields = AjaxMultipleChoiceField(label=_(u'Regular fields'), required=False, choices=(), widget=OrderedMultipleChoiceWidget)
    #custom_fields  = AjaxMultipleChoiceField(label=_(u'Custom fields'),  required=False, choices=(), widget=OrderedMultipleChoiceWidget)
    #related_fields = AjaxMultipleChoiceField(label=_(u'Related fields'), required=False, choices=(), widget=OrderedMultipleChoiceWidget)
    #relations      = AjaxMultipleChoiceField(label=_(u'Relations'),      required=False, choices=(), widget=OrderedMultipleChoiceWidget)
    #functions      = AjaxMultipleChoiceField(label=_(u'Functions'),      required=False, choices=(), widget=OrderedMultipleChoiceWidget)

    #blocks = CremeEntityForm.blocks.new(
        #('hf_block',         _(u'Select from a existing view : '), ['hf']),
        #('fields_block',     _(u'Or'), ['regular_fields', 'related_fields', 'custom_fields','relations', 'functions']),
        #('aggregates_block', _(u'Calculated values'), [aggregate.name for aggregate in field_aggregation_registry.itervalues()]),
    #)

    class Meta(CremeEntityForm.Meta):
        model = Report

    #def __init__(self, *args, **kwargs):
        #super(CreateForm, self).__init__(*args, **kwargs)
        #fields = self.fields

        #self.aggregates = list(field_aggregation_registry.itervalues())#Convert to list to reuse it in template

        #for aggregate in self.aggregates:
            #fields[aggregate.name] = AjaxMultipleChoiceField(label=_(aggregate.title), required=False, choices=(), widget=OrderedMultipleChoiceWidget)

        #To hande a validation error get ct_id data to rebuild all ?

    def clean(self):
        cleaned_data = self.cleaned_data
        #get_data     = cleaned_data.get
        #fields       = self.fields

        #hf             = get_data('hf')
        #regular_fields = get_data('regular_fields')
        #related_fields = get_data('related_fields')
        #custom_fields  = get_data('custom_fields')
        #relations      = get_data('relations')
        #functions      = get_data('functions')

        #aggregates = self.aggregates

        #is_one_aggregate_selected = False
        #for aggregate in aggregates:
            #for data in get_data(aggregate.name):
                #is_one_aggregate_selected |= bool(data)

        #if not hf and not (regular_fields or related_fields or custom_fields or relations or functions or is_one_aggregate_selected):
            #rfield_fields = ['regular_fields', 'related_fields', 'custom_fields', 'relations', 'functions']
            #rfield_fields.extend(aggregate.name for aggregate in aggregates)
            #raise ValidationError(ugettext(u"You must select an existing view, or at least one field from : %s") %
                                    #u", ".join(unicode(fields[f].label) for f in rfield_fields)
                                 #)

        if not self._errors:
            get_data = cleaned_data.get
            ct = get_data('ct')
            hf = get_data('hf')

            if hf.entity_type != ct:
                self.errors['hf'] = ErrorList([ugettext(u'Select a valid choice. That choice is not one of the available choices.')])

            efilter = get_data('filter')
            if efilter and efilter.entity_type != ct:
                self.errors['filter'] = ErrorList([ugettext(u'Select a valid choice. That choice is not one of the available choices.')])

        return cleaned_data

    #def save(self, *args, **kwargs):
        #report = super(CreateForm, self).save(*args, **kwargs)
        #report_fields = []
        #get_data = self.cleaned_data.get
        #hf = get_data('hf')

        #if hf is not None:
            ##Have to build from an existant header filter
            #field_get_instance_from_hf_item = Field.get_instance_from_hf_item

            #for hf_item in hf.items:
                #f = field_get_instance_from_hf_item(hf_item)
                #f.save()
                #report_fields.append(f)
        #else:
            #model = report.ct.model_class()
            #i = 1

            #for regular_field in get_data('regular_fields'):
                #report_fields.append(save_hfi_field(model, regular_field, i))
                #i += 1

            #for related_field in get_data('related_fields'):
                #report_fields.append(save_hfi_related_field(model, related_field, i))
                #i += 1

            #cf_ids = get_data('custom_fields')
            #if cf_ids:
                #cfields = CustomField.objects.filter(content_type=report.ct).in_bulk(cf_ids)

                #for cf_id in cf_ids:
                    #try:
                        #cfield = cfields[int(cf_id)]
                    #except (ValueError, KeyError):
                        #logger.exception('CreateForm.save()')
                    #else:
                        #report_fields.append(save_hfi_cf(cfield, i))
                        #i += 1

            #for relation in get_data('relations'):
                #report_fields.append(save_hfi_relation(relation, i))
                #i += 1

            #for function in get_data('functions'):
                #report_fields.append(save_hfi_function(model, function, i))
                #i += 1

            #for aggregate in self.aggregates:
                #for calculated_column in get_data(aggregate.name):
                    #title = _get_hfi_calculated_title(aggregate, calculated_column, model)
                    #report_fields.append(save_hfi_calculated(calculated_column, title, i))
                    #i += 1

        #report.columns = report_fields

        #return report

    _TYPE_TRANSLATION_MAP = {
            EntityCellRegularField.type_id:     RFT_FIELD,
            EntityCellCustomField.type_id:      RFT_CUSTOM,
            EntityCellFunctionField.type_id:    RFT_FUNCTION,
            EntityCellRelation.type_id:         RFT_RELATION,
        }

    @commit_on_success
    def save(self, *args, **kwargs):
        report = super(CreateForm, self).save(*args, **kwargs)
        build_field = partial(Field.objects.create, report=report)

        for i, cell in enumerate(self.cleaned_data['hf'].cells, start=1):
            #TODO: check in clean() that id is OK
            build_field(name=cell.value, title=cell.title, order=i,
                        type=self._TYPE_TRANSLATION_MAP[cell.type_id],
                       )

        return report


class EditForm(CremeEntityForm):
    class Meta:
        model = Report
        exclude = CremeEntityForm.Meta.exclude + ('ct',)

    def __init__(self, *args, **kwargs):
        super(EditForm, self).__init__(*args, **kwargs)
        filter_f = self.fields['filter']
        filter_f.empty_label = ugettext(u'All')
        filter_f.queryset = filter_f.queryset.filter(entity_type=self.instance.ct)


class LinkFieldToReportForm(CremeForm):
    report = CreatorEntityField(label=_(u"Sub-report linked to the column"), model=Report)

    def __init__(self, field, ctypes, *args, **kwargs):
        super(LinkFieldToReportForm, self).__init__(*args, **kwargs)
        self.rfield = field
        report = field.report
        q_filter = {'~id__in': [r.id for r in chain(report.get_ascendants_reports(), [report])]}

        if ctypes:
            q_filter['ct__in'] = [ct.id for ct in ctypes]

        self.fields['report'].q_filter = q_filter

    def save(self):
        rfield = self.rfield
        rfield.sub_report = self.cleaned_data['report']
        rfield.save()


class AddFieldToReportForm(CremeForm):
    regular_fields = MultipleChoiceField(label=_(u'Regular fields'), required=False, choices=(), widget=OrderedMultipleChoiceWidget)
    related_fields = MultipleChoiceField(label=_(u'Related fields'), required=False, choices=(), widget=OrderedMultipleChoiceWidget)
    custom_fields  = MultipleChoiceField(label=_(u'Custom fields'),  required=False, choices=(), widget=OrderedMultipleChoiceWidget)
    relations      = MultipleChoiceField(label=_(u'Relations'),      required=False, choices=(), widget=OrderedMultipleChoiceWidget)
    functions      = MultipleChoiceField(label=_(u'Functions'),      required=False, choices=(), widget=OrderedMultipleChoiceWidget)

    blocks = CremeEntityForm.blocks.new(
        ('aggregates_block', _(u'Calculated values'), [aggregate.name for aggregate in field_aggregation_registry.itervalues()]),
    )

    def __init__(self, entity, *args, **kwargs):
        self.report = entity
        super(AddFieldToReportForm, self).__init__(*args, **kwargs)
        ct = entity.ct
        model = ct.model_class()

        fields = self.fields
        self.rfields = rfields = list(entity.columns) #pool of Fields
        initial_data = defaultdict(list)

        for rfield in rfields:
            initial_data[rfield.type].append(rfield.name)

        regular_fields_f = fields['regular_fields']
        regular_fields_f.choices = ModelFieldEnumerator(model, deep=1) \
                                        .filter(viewable=True) \
                                        .choices()
        regular_fields_f.initial = initial_data[RFT_FIELD]

        related_fields_f = fields['related_fields']
        related_fields_f.choices = Report.get_related_fields_choices(model)
        related_fields_f.initial = initial_data[RFT_RELATED]

        custom_fields_f = fields['custom_fields']
        self.custom_fields = cfields = dict((cf.id, cf) for cf in CustomField.objects.filter(content_type=ct)) #TODO: remove when title is now more store in Field
        custom_fields_f.choices = [(str(cf.id), cf.name) for cf in cfields.itervalues()]
        custom_fields_f.initial = initial_data[RFT_CUSTOM]

        relations_f = fields['relations']
        self.rtypes = rtypes = OrderedDict(RelationType.get_compatible_ones(ct)
                                                       .order_by('predicate') #TODO: unicode collation
                                                       .values_list('id', 'predicate')
                                          )
        relations_f.choices = rtypes.items()
        relations_f.initial = initial_data[RFT_RELATION]

        function_fields_f = fields['functions']
        function_fields_f.choices = [(f.name, f.verbose_name) for f in model.function_fields] #TODO: unicode collation ??
        function_fields_f.initial = initial_data[RFT_FUNCTION]

        self._set_aggregate_fields(model, initial_data=initial_data[RFT_CALCULATED])

    def _set_aggregate_fields(self, model, initial_data=None):
        fields = self.fields
        authorized_fields = field_aggregation_registry.authorized_fields

        for aggregate in field_aggregation_registry.itervalues():
            pattern = aggregate.pattern
            choices = [(pattern % f_name, f_vname)
                            for f_name, f_vname in ModelFieldEnumerator(model, deep=0)
                                                    .filter((lambda f: isinstance(f, authorized_fields)),
                                                            viewable=True,
                                                           )
                                                    .choices()
                      ]

            choices.extend(get_aggregate_custom_fields(model, pattern))

            fields[aggregate.name] = MultipleChoiceField(label=aggregate.title,
                                                         required=False, choices=choices,
                                                         widget=OrderedMultipleChoiceWidget,
                                                         initial=initial_data,
                                                        )

    @commit_on_success
    def save(self):
        get_data = self.cleaned_data.get
        report = self.report

        old_rfields = self.rfields
        order = count(1)

        def add_rfield(name, ftype):
            rfield = Field(pk=old_rfields.pop(0).pk if old_rfields else None,
                           report=report, name=name, type=ftype,
                           order=order.next(),
                          )
            rfield.save() #TODO: only if different than the old one

        for field_name in get_data('regular_fields'):
            add_rfield(name=field_name, ftype=RFT_FIELD)

        for related_field_name in get_data('related_fields'):
            add_rfield(name=related_field_name, ftype=RFT_RELATED)

        for cf_id in get_data('custom_fields'):
            cfield = self.custom_fields[int(cf_id)]
            add_rfield(name=cfield.id, ftype=RFT_CUSTOM)

        for rtype_id in get_data('relations'):
            add_rfield(name=rtype_id, ftype=RFT_RELATION)

        for funfield_name in get_data('functions'):
            add_rfield(name=funfield_name, ftype=RFT_FUNCTION)

        for aggregation in field_aggregation_registry.itervalues():
            for aggregate_id in get_data(aggregation.name):
                add_rfield(name=aggregate_id, ftype=RFT_CALCULATED)

        Field.objects.filter(pk__in=[rfield.id for rfield in old_rfields]).delete()


class DateReportFilterForm(CremeForm):
    doc_type    = ChoiceField(label=_(u'Extension'), required=False, choices=())
    date_field  = ChoiceField(label=_(u'Date field'), required=False, choices=())
    date_filter = DateRangeField(label=_(u'Date filter'), required=False)

    def __init__(self, report, *args, **kwargs):
        super(DateReportFilterForm, self).__init__(*args, **kwargs)
        fields = self.fields

        date_field_choices = [("", _(u"None"))]
        date_field_choices.extend([(field.name, field.verbose_name)
                                            for field in get_date_fields(report.ct.model_class())
                                       ])
        fields['date_field'].choices = date_field_choices

        choices = [(backend.id, backend.verbose_name)
                        for backend in export_backend_registry.iterbackends()
                  ]
        if choices:
            doc_type = fields['doc_type']
            doc_type.choices = choices
            try:
                doc_type.initial = choices[0][0]
            except IndexError:
                pass

    def get_q_dict(self):
        cdata = self.cleaned_data
        if cdata:
            date_field = cdata['date_field']
            if date_field:
                return cdata['date_filter'].get_q_dict(date_field, now())
        return None

    def get_dates(self):
        cdata = self.cleaned_data
        if cdata and cdata['date_field']:
            date_filter = cdata['date_filter']
            if date_filter:
                return date_filter.get_dates(now())
        return None, None

    def clean(self):
        super(DateReportFilterForm, self).clean()
        cdata = self.cleaned_data
        if cdata['date_field']:
            start, end = self.get_dates()
            if not start and not end:
                self.errors['date_filter'] = ErrorList([ugettext(u"If you chose a Date field, and select «customized» you have to specify a start date and/or an end date.")])
        return cdata

    @property
    def forge_url_data(self):
        cdata = self.cleaned_data
        if cdata:
            get_cdata = cdata.get
            date_field = get_cdata('date_field')
            if date_field:
                data = ['field=%s' % date_field,
                        'range_name=%s' % get_cdata('date_filter').name
                       ]

                start, end = self.get_dates()

                if start is not None:
                    data.append('start=%s' % encode_datetime(start))
                if end is not None:
                    data.append('end=%s' % encode_datetime(end))

                return "?%s" % "&".join(data)
        return ""

    #def save(self, *args, **kwargs):
        #return self.cleaned_data
