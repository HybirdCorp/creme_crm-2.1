# -*- coding: utf-8 -*-

################################################################################
#    Creme is a free/open-source Customer Relationship Management software
#    Copyright (C) 2009-2010  Hybird
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

from django.db.models import ForeignKey, CharField, PositiveSmallIntegerField, IntegerField, DecimalField, DateTimeField, BooleanField, ManyToManyField
from django import forms
from django.utils.translation import ugettext, ugettext_lazy as _
from django.utils.datastructures import SortedDict as OrderedDict #use python2.6 OrderedDict later.....
from django.contrib.contenttypes.models import ContentType

from base import CremeModel
from entity import CremeEntity


__all__ = ('CustomField', 'CustomFieldValue',
           'CustomFieldInteger', 'CustomFieldFloat', 'CustomFieldBoolean',
           'CustomFieldString', 'CustomFieldDateTime',
           'CustomFieldEnumValue', 'CustomFieldEnum', 'CustomFieldMultiEnum')


class CustomField(CremeModel):
    INT         = 1
    FLOAT       = 2
    BOOL        = 3
    STR         = 10
    DATE        = 20
    ENUM        = 100
    MULTI_ENUM  = 101

    name          = CharField(_(u'Nom du champ'), max_length=100)
    content_type  = ForeignKey(ContentType, verbose_name=_(u'Resource associée'))
    field_type    = PositiveSmallIntegerField(_(u'Type du champ')) #see INT, FLOAT etc...
    #default_value = CharField(_(u'Valeur par defaut'), max_length=100, blank=True, null=True)
    #extra_args    = CharField(max_length=500, blank=True, null=True)
    #required      = BooleanField(defaut=False) ????

    class Meta:
       app_label = 'creme_core'
       verbose_name = _(u'Champ personnalisé')
       verbose_name_plural = _(u'Champs personnalisés')
       ordering = ('id',)

    def __unicode__(self):
        return self.name

    def delete(self):
        for value_class in _TABLES.itervalues():
            value_class.objects.filter(custom_field=self).delete()
        self.customfieldenumvalue_set.all().delete() #Beware: don't call the CustomFieldEnumValue.delete() to avoid loop
        super(CustomField, self).delete()

    def type_verbose_name(self):
        return _TABLES[self.field_type].verbose_name

    def get_value_class(self):
        return _TABLES[self.field_type]

    def get_formfield(self, custom_value):
        return self.get_value_class().get_formfield(self, custom_value)

    def get_pretty_value(self, entity_id):
        """Return unicode object containing the human readable value of this custom field for an entity
        It manages CustomField which type is ENUM.
        """
        #TODO: select_related() for enum ???
        cf_values = self.get_value_class().objects.filter(custom_field=self.id, entity=entity_id)

        return unicode(cf_values[0]) if cf_values else u''

    @staticmethod
    def get_custom_values_map(entities, custom_fields):
        """
        @return { Entity -> { CustomField's id -> CustomValue } }
        """
        cfield_map = defaultdict(list)
        for cfield in custom_fields:
            cfield_map[cfield.field_type].append(cfield)

        cvalues_map = defaultdict(lambda: defaultdict(list))
        entities = [e.id for e in entities] #NB: 'list(entities)' ==> made strangely a query for every entity ;(

        for field_type, cfields_list in cfield_map.iteritems():
            for cvalue in _TABLES[field_type]._get_4_entities(entities, cfields_list):
                cvalues_map[cvalue.entity_id][cvalue.custom_field_id] = cvalue

        return cvalues_map


class CustomFieldValue(CremeModel):
    custom_field = ForeignKey(CustomField)
    entity       = ForeignKey(CremeEntity)
    #value       = FoobarField()  --> implement in inherited classes

    class Meta:
        abstract = True

    def __unicode__(self):
        return unicode(self.value)

    @classmethod
    def _get_4_entities(cls, entities, cfields):
        """Retrieve all custom values for a list of custom fields with the same type.
        Trick: overload me to optimise the query (eg: use a select_related())
        """
        return cls.objects.filter(custom_field__in=cfields, entity__in=entities)

    @classmethod
    def get_related_name(cls):
        return cls.__name__.lower()

    @staticmethod
    def delete_all(entity):
        cf_types = set(CustomField.objects.filter(content_type=entity.entity_type_id)\
                                          .values_list('field_type', flat=True))

        for cf_type in cf_types:
            for cvalue in _TABLES[cf_type].objects.filter(entity=entity):
                cvalue.delete()

    @staticmethod
    def _build_formfield(custom_field, formfield):
        pass

    def _set_formfield_value(self, field):
        field.initial = self.value

    @staticmethod
    def get_formfield_class(): #overload meeee
        return forms.Field

    @classmethod
    def get_formfield(cls, custom_field, custom_value):
        field = cls.get_formfield_class()(label=custom_field.name, required=False)
        cls._build_formfield(custom_field, field)

        if custom_value:
            custom_value._set_formfield_value(field)

        return field

    def set_value_n_save(self, value):
        if self.value != value:
            self.value = value
            self.save()


class CustomFieldString(CustomFieldValue):
    value = CharField(max_length=100)

    verbose_name = _(u'Chaîne de caractères')

    class Meta:
        app_label = 'creme_core'

    def __unicode__(self):
        return self.value

    @staticmethod
    def get_formfield_class():
        return forms.CharField


class CustomFieldInteger(CustomFieldValue):
    value = IntegerField()

    verbose_name = _(u'Nombre entier')

    class Meta:
        app_label = 'creme_core'

    @staticmethod
    def get_formfield_class():
        return forms.IntegerField


class CustomFieldFloat(CustomFieldValue):
    value = DecimalField(max_digits=4, decimal_places=2)

    verbose_name = _(u'Nombre à virgule')

    class Meta:
        app_label = 'creme_core'

    @staticmethod
    def get_formfield_class():
        return forms.DecimalField


class CustomFieldDateTime(CustomFieldValue):
    value = DateTimeField()

    verbose_name = _(u'Date')

    class Meta:
        app_label = 'creme_core'

    @staticmethod
    def get_formfield_class():
        from creme_core.forms.fields import CremeDateTimeField #avoid cyclic import
        return CremeDateTimeField


class CustomFieldBoolean(CustomFieldValue):
    value = BooleanField()

    verbose_name = _(u'Booléen (2 valeurs: Oui/Non)')

    class Meta:
        app_label = 'creme_core'

    def __unicode__(self):
        return ugettext(u'Oui') if self.value else ugettext(u'Non')

    @staticmethod
    def get_formfield_class():
        return forms.BooleanField


class CustomFieldEnumValue(CremeModel):
    custom_field = ForeignKey(CustomField, related_name='customfieldenumvalue_set')
    value        = CharField(max_length=100)

    class Meta:
        app_label = 'creme_core'

    def __unicode__(self):
        return self.value

    def delete(self):
        CustomFieldEnum.objects.filter(custom_field=self.custom_field_id, value=str(self.id)).delete()
        super(CustomFieldEnumValue, self).delete()


class CustomFieldEnum(CustomFieldValue):
    value = ForeignKey(CustomFieldEnumValue)

    verbose_name = _(u'Liste de choix')

    class Meta:
        app_label = 'creme_core'

    @staticmethod
    def get_formfield_class():
        return forms.ChoiceField

    @classmethod
    def _get_4_entities(cls, entities, cfields):
        return cls.objects.filter(custom_field__in=cfields, entity__in=entities).select_related('value')

    @staticmethod
    def _build_formfield(custom_field, formfield):
        choices = [('', '-------')]
        choices += CustomFieldEnumValue.objects.filter(custom_field=custom_field).values_list('id', 'value')
        formfield.choices = choices

    def _set_formfield_value(self, field):
        field.initial = self.value_id

    def set_value_n_save(self, value):
        value = int(value)
        if self.value_id != value:
            self.value_id = value
            self.save()


class CustomFieldMultiEnum(CustomFieldValue):
    value = ManyToManyField(CustomFieldEnumValue)

    verbose_name = _(u'Liste de choix (multi sélection)')

    _enumvalues = None

    class Meta:
        app_label = 'creme_core'

    def __unicode__(self):
        #output = ['<ul>']
        #output.extend(u'<li>%s</li>' % val for val in self.value.all())
        #output.append('</ul>')
        #return u''.join(output)
        return u' / '.join(unicode(val) for val in self.get_enumvalues())

    @staticmethod
    def get_formfield_class():
        return forms.MultipleChoiceField

    @classmethod
    def _get_4_entities(cls, entities, cfields):
        #TODO: for a m2m select_related() doesn't work -> can fill the enumvalues cache easily (must use BaseQuery.join in query.py ....)
        return cls.objects.filter(custom_field__in=cfields, entity__in=entities)

    @staticmethod
    def _build_formfield(custom_field, formfield):
        formfield.choices = CustomFieldEnumValue.objects.filter(custom_field=custom_field).values_list('id', 'value')

    def get_enumvalues(self):
        if self._enumvalues is None:
            self._enumvalues = self.value.all()

        return self._enumvalues

    def _set_formfield_value(self, field):
        field.initial = self.value.all().values_list('id', flat=True)

    def set_value_n_save(self, value):
        if not self.pk:
            self.save() #M2M field need a pk

        self.value = value


_TABLES = OrderedDict([
    (CustomField.INT,        CustomFieldInteger),
    (CustomField.FLOAT,      CustomFieldFloat),
    (CustomField.BOOL,       CustomFieldBoolean),
    (CustomField.STR,        CustomFieldString),
    (CustomField.DATE,       CustomFieldDateTime),
    (CustomField.ENUM,       CustomFieldEnum),
    (CustomField.MULTI_ENUM, CustomFieldMultiEnum),
])
