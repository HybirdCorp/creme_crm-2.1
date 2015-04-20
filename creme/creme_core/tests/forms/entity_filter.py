# -*- coding: utf-8 -*-
try:
    from json import loads as jsonloads, dumps as json_encode

    from django.utils.translation import ugettext as _

    from ..fake_models import (FakeContact as Contact, FakeCivility as Civility,
            FakeOrganisation as Organisation)
    from .base import FieldTestCase
    from creme.creme_core.forms.entity_filter import *
    from creme.creme_core.models.custom_field import CustomFieldEnumValue

#    from creme.persons.models import Organisation, Contact, Civility
except Exception as e:
    print('Error in <%s>: %s' % (__name__, e))


__all__ = ('RegularFieldsConditionsFieldTestCase', 'DateFieldsConditionsFieldTestCase',
           'CustomFieldsConditionsFieldTestCase', 'DateCustomFieldsConditionsFieldTestCase',
           'PropertiesConditionsFieldTestCase', 'RelationsConditionsFieldTestCase',
           'RelationSubfiltersConditionsFieldTestCase',
          )

class RegularFieldsConditionsFieldTestCase(FieldTestCase):
    CONDITION_FIELD_JSON_FMT = '[{"field": {"name": "%(name)s"}, "operator": {"id": "%(operator)s"}, "value": %(value)s}]'

    @classmethod
    def setUpClass(cls):
        FieldTestCase.setUpClass()
        cls.autodiscover()
#        cls.populate('persons')
        cls.populate('creme_core')

    def test_clean_empty_required(self):
        clean = RegularFieldsConditionsField(required=True).clean
        self.assertFieldValidationError(RegularFieldsConditionsField, 'required', clean, None)
        self.assertFieldValidationError(RegularFieldsConditionsField, 'required', clean, "")
        self.assertFieldValidationError(RegularFieldsConditionsField, 'required', clean, "[]")

    def test_clean_empty_not_required(self):
        field = RegularFieldsConditionsField(required=False)

        with self.assertNoException():
            value = field.clean(None)

        self.assertEqual([], value)

    def test_clean_invalid_data_type(self):
        clean = RegularFieldsConditionsField().clean
        self.assertFieldValidationError(RegularFieldsConditionsField, 'invalidtype', clean, '"this is a string"')
        self.assertFieldValidationError(RegularFieldsConditionsField, 'invalidtype', clean, '"{}"')
        self.assertFieldValidationError(RegularFieldsConditionsField, 'invalidtype', clean, '{"foobar":{"operator":"3","name":"first_name","value":"Rei"}}')
        self.assertFieldValidationError(RegularFieldsConditionsField, 'invalidtype', clean, '1')

    def test_clean_invalid_data(self):
        clean = RegularFieldsConditionsField(model=Contact).clean
        self.assertFieldValidationError(RegularFieldsConditionsField, 'invalidformat', clean,
                                        '[{"operator": {"id": "notanumber"}, "field": {"name":"first_name"}, "value": "Rei"}]'
                                       )

    def test_clean_incomplete_data_required(self):
        clean = RegularFieldsConditionsField(model=Contact).clean
        EQUALS = EntityFilterCondition.EQUALS
        self.assertFieldValidationError(RegularFieldsConditionsField, 'invalidvalue',    clean, '[{"operator": {"id": "%s"}, "field": {"name": "first_name"}}]' % EQUALS)
        self.assertFieldValidationError(RegularFieldsConditionsField, 'invalidfield',    clean, '[{"operator": {"id": "%s"}, "value": "Rei"}]' % EQUALS)
        self.assertFieldValidationError(RegularFieldsConditionsField, 'invalidoperator', clean, '[{"field": {"name": "first_name"}, "value": "Rei"}]')

    def test_clean_invalid_field(self):
        clean = RegularFieldsConditionsField(model=Contact).clean
        format_str = self.CONDITION_FIELD_JSON_FMT

        self.assertFieldValidationError(RegularFieldsConditionsField, 'invalidfield', clean,
                                        format_str % {'operator':  EntityFilterCondition.EQUALS,
                                                      'name':  '   boobies_size', #<---
                                                      'value':     90,
                                                     }
                                        )
        self.assertFieldValidationError(RegularFieldsConditionsField, 'invalidfield', clean,
                                        format_str % {'operator': EntityFilterCondition.IEQUALS,
                                                      'name':     'is_deleted',
                                                      'value':    '"Faye"',
                                                     }
                                        )
        self.assertFieldValidationError(RegularFieldsConditionsField, 'invalidfield', clean,
                                        format_str % {'operator': EntityFilterCondition.IEQUALS,
                                                      'name':     'created',
                                                      'value':    '"2011-5-12"',
                                                     }
                                        )
        self.assertFieldValidationError(RegularFieldsConditionsField, 'invalidfield', clean,
                                        format_str % {'operator': EntityFilterCondition.IEQUALS,
                                                      'name':     'civility__id',
                                                      'value':    5,
                                                     }
                                        )
        self.assertFieldValidationError(RegularFieldsConditionsField, 'invalidfield', clean,
                                        format_str % {'operator': EntityFilterCondition.IEQUALS,
                                                      'name':     'image__id',
                                                      'value':    5,
                                                     }
                                       )
        self.assertFieldValidationError(RegularFieldsConditionsField, 'invalidfield', clean,
                                        format_str % {'operator': EntityFilterCondition.IEQUALS,
                                                      'name':     'image__is_deleted',
                                                      'value':    5,
                                                     }
                                       )
        self.assertFieldValidationError(RegularFieldsConditionsField, 'invalidfield', clean,
                                        format_str % {'operator': EntityFilterCondition.IEQUALS,
                                                      'name':     'image__modified',
                                                      'value':    '"2011-5-12"',
                                                     }
                                       )
        #TODO: M2M

    def test_clean_invalid_operator(self):
        clean = RegularFieldsConditionsField(model=Contact).clean
        self.assertFieldValidationError(RegularFieldsConditionsField, 'invalidoperator', clean,
                                        self.CONDITION_FIELD_JSON_FMT % {
                                                'operator': EntityFilterCondition.EQUALS + 1000, # <--
                                                'name':     'first_name',
                                                'value':    '"Nana"',
                                            }
                                       )

    def test_clean_invalid_fk_id(self):
        """FK field with invalid id"""

        clean = RegularFieldsConditionsField(model=Contact).clean
        operator = EntityFilterCondition.EQUALS
        name = 'civility'
        value = 'unknown'
        err = self.assertFieldRaises(ValidationError, clean,
                                     self.CONDITION_FIELD_JSON_FMT % {
                                             'operator': operator,
                                             'name':     name,
                                             'value':    '"' + value + '"',
                                         }
                                     )[0]

        self.assertEqual(err.messages[0], unicode([_(u'Select a valid choice. That choice is not one of the available choices.')]));

    def test_iequals_condition(self):
        clean = RegularFieldsConditionsField(model=Contact).clean
        operator = EntityFilterCondition.IEQUALS
        name = 'first_name'
        value = 'Faye'
        conditions = clean(self.CONDITION_FIELD_JSON_FMT % {
                                 'operator': operator,
                                 'name':     name,
                                 'value':    '"' + value + '"',
                             }
                          )
        self.assertEqual(1, len(conditions))

        condition = conditions[0]
        self.assertEqual(EntityFilterCondition.EFC_FIELD,           condition.type)
        self.assertEqual(name,                                      condition.name)
        self.assertEqual({'operator': operator, 'values': [value]}, condition.decoded_value)

    def test_iequals_condition_multiple_as_string(self):
        clean = RegularFieldsConditionsField(model=Contact).clean
        operator = EntityFilterCondition.IEQUALS
        name = 'first_name'
        faye_name = 'Faye'
        ed_name = 'Ed'
        conditions = clean(self.CONDITION_FIELD_JSON_FMT % {
                                 'operator': operator,
                                 'name':     name,
                                 'value':    '"' + faye_name + ',' + ed_name + '"',
                             }
                          )
        self.assertEqual(1, len(conditions))

        condition = conditions[0]
        self.assertEqual(EntityFilterCondition.EFC_FIELD, condition.type)
        self.assertEqual(name,                            condition.name)
        self.assertEqual({'operator': operator, 'values': [faye_name, ed_name]}, condition.decoded_value)

    def test_iequals_condition_multiple_as_list(self):
        clean = RegularFieldsConditionsField(model=Contact).clean
        operator = EntityFilterCondition.IEQUALS
        name = 'first_name'
        faye_name = 'Faye'
        ed_name = 'Ed'
        conditions = clean(self.CONDITION_FIELD_JSON_FMT % {
                                 'operator': operator,
                                 'name':     name,
                                 'value':    json_encode([faye_name, ed_name]),
                             }
                          )
        self.assertEqual(1, len(conditions))

        condition = conditions[0]
        self.assertEqual(EntityFilterCondition.EFC_FIELD, condition.type)
        self.assertEqual(name,                            condition.name)
        self.assertEqual({'operator': operator, 'values': [faye_name, ed_name]}, condition.decoded_value)

    def test_isempty_condition(self): #ISEMPTY -> boolean
        clean = RegularFieldsConditionsField(model=Contact).clean
        operator = EntityFilterCondition.ISEMPTY
        name = 'description'
        conditions = clean(self.CONDITION_FIELD_JSON_FMT % {
                                 'operator': operator,
                                 'name':     name,
                                 'value':    'true',
                             }
                          )
        self.assertEqual(1, len(conditions))

        condition = conditions[0]
        self.assertEqual(EntityFilterCondition.EFC_FIELD,           condition.type)
        self.assertEqual(name,                                      condition.name)
        self.assertEqual({'operator': operator, 'values': [True]}, condition.decoded_value)

    def test_isnotempty_condition(self):
        "ISEMPTY -> boolean"
        clean = RegularFieldsConditionsField(model=Contact).clean
        operator = EntityFilterCondition.ISEMPTY
        name = 'description'
        conditions = clean(self.CONDITION_FIELD_JSON_FMT % {
                                 'operator': operator,
                                 'name':     name,
                                 'value':    'false',
                             }
                          )
        self.assertEqual(1, len(conditions))

        condition = conditions[0]
        self.assertEqual(EntityFilterCondition.EFC_FIELD,           condition.type)
        self.assertEqual(name,                                      condition.name)
        self.assertEqual({'operator': operator, 'values': [False]}, condition.decoded_value)

    def test_fk_subfield(self):
        """FK subfield"""
        clean = RegularFieldsConditionsField(model=Contact).clean
        operator = EntityFilterCondition.ISTARTSWITH
        name = 'civility__title'
        value = 'Miss'
        conditions = clean(self.CONDITION_FIELD_JSON_FMT % {
                                 'operator': operator,
                                 'name':     name,
                                 'value':    '"' + value + '"',
                             }
                          )
        self.assertEqual(1, len(conditions))

        condition = conditions[0]
        self.assertEqual(EntityFilterCondition.EFC_FIELD,           condition.type)
        self.assertEqual(name,                                      condition.name)
        self.assertEqual({'operator': operator, 'values': [value]}, condition.decoded_value)

    def test_fk(self):
        "FK field"
        clean = RegularFieldsConditionsField(model=Contact).clean
        operator = EntityFilterCondition.EQUALS
        name = 'civility'
        value = Civility.objects.all()[0].pk
        conditions = clean(self.CONDITION_FIELD_JSON_FMT % {
                                 'operator': operator,
                                 'name':     name,
                                 'value':    value,
                             }
                          )
        self.assertEqual(1, len(conditions))

        condition = conditions[0]
        self.assertEqual(EntityFilterCondition.EFC_FIELD,           condition.type)
        self.assertEqual(name,                                      condition.name)
        self.assertEqual({'operator': operator, 'values': [str(value)]}, condition.decoded_value)

    def test_multiple_fk_as_string(self):
        clean = RegularFieldsConditionsField(model=Contact).clean
        operator = EntityFilterCondition.EQUALS
        name = 'civility'
        values = [c.pk for c in Civility.objects.all()]
        conditions = clean(self.CONDITION_FIELD_JSON_FMT % {
                                 'operator': operator,
                                 'name':     name,
                                 'value':    '"' + ','.join(str(v) for v in values) + '"',
                             }
                          )
        self.assertEqual(1, len(conditions))

        condition = conditions[0]
        self.assertEqual(EntityFilterCondition.EFC_FIELD,           condition.type)
        self.assertEqual(name,                                      condition.name)
        self.assertEqual({'operator': operator, 'values': [str(v) for v in values]}, condition.decoded_value)

    def test_multiple_fk_as_list(self):
        clean = RegularFieldsConditionsField(model=Contact).clean
        operator = EntityFilterCondition.EQUALS
        name = 'civility'
        values = [str(c.pk) for c in Civility.objects.all()]
        conditions = clean(self.CONDITION_FIELD_JSON_FMT % {
                                 'operator': operator,
                                 'name':     name,
                                 'value':    json_encode(values),
                             }
                          )
        self.assertEqual(1, len(conditions))

        condition = conditions[0]
        self.assertEqual(EntityFilterCondition.EFC_FIELD,           condition.type)
        self.assertEqual(name,                                      condition.name)
        self.assertEqual({'operator': operator, 'values': [str(v) for v in values]}, condition.decoded_value)

    def test_choicetypes(self):
        "Field choice types"
        field_choicetype = FieldConditionWidget.field_choicetype
        get_field = Contact._meta.get_field_by_name

        self.assertEqual(field_choicetype(get_field('civility')[0]), 'enum__null')

        self.assertEqual(field_choicetype(get_field('birthday')[0]), 'date__null')
        self.assertEqual(field_choicetype(get_field('created')[0]),  'date')

        #self.assertEqual(field_choicetype(get_field('billing_address')[0]),  'fk__null')
        self.assertEqual(field_choicetype(get_field('address')[0]),  'fk__null')

        self.assertEqual(field_choicetype(get_field('user')[0]),     'user')
        self.assertEqual(field_choicetype(get_field('is_user')[0]),  'user__null')

#     def test_ok02(self):
#         "ISEMPTY -> boolean"
#         clean = RegularFieldsConditionsField(model=Contact).clean
#         operator = EntityFilterCondition.ISEMPTY
#         name = 'description'
#         conditions = clean('[{"name": "%(name)s", "operator": "%(operator)s", "value": false}]' % {
#                                  'operator': operator,
#                                  'name':     name,
#                              }
#                           )
#         self.assertEqual(1, len(conditions))
# 
#         condition = conditions[0]
#         self.assertEqual(EntityFilterCondition.EFC_FIELD,           condition.type)
#         self.assertEqual(name,                                      condition.name)
#         self.assertEqual({'operator': operator, 'values': [False]}, condition.decoded_value)
# 
#     def test_ok03(self):
#         "FK field"
#         clean = RegularFieldsConditionsField(model=Contact).clean
#         operator = EntityFilterCondition.ISTARTSWITH
#         name = 'civility__title'
#         value = 'Miss'
#         conditions = clean('[{"name": "%(name)s", "operator": "%(operator)s", "value": "%(value)s"}]' % {
#                                  'operator': operator,
#                                  'name':     name,
#                                  'value':    value,
#                              }
#                           )
#         self.assertEqual(1, len(conditions))
# 
#         condition = conditions[0]
#         self.assertEqual(EntityFilterCondition.EFC_FIELD,           condition.type)
#         self.assertEqual(name,                                      condition.name)
#         self.assertEqual({'operator': operator, 'values': [value]}, condition.decoded_value)

    def test_iendswith_valuelist(self):
        "Multi values"
        clean = RegularFieldsConditionsField(model=Contact).clean
        operator = EntityFilterCondition.IENDSWITH
        name = 'last_name'
        values = ['nagi', 'sume']
        conditions = clean(self.CONDITION_FIELD_JSON_FMT % {
                                 'operator': operator,
                                 'name':     name,
                                 'value':    '"' + ','.join(values) + ',' + '"',
                             }
                          )
        self.assertEqual(1, len(conditions))

        condition = conditions[0]
        self.assertEqual(EntityFilterCondition.EFC_FIELD,          condition.type)
        self.assertEqual(name,                                     condition.name)
        self.assertEqual({'operator': operator, 'values': values}, condition.decoded_value)

    def test_many2many_subfield(self):
        "M2M field"
        clean = RegularFieldsConditionsField(model=Contact).clean
        operator = EntityFilterCondition.IEQUALS
        name = 'languages__name'
        value = 'French'
        conditions = clean(self.CONDITION_FIELD_JSON_FMT % {
                                 'operator': operator,
                                 'name':     name,
                                 'value':    '"' + value + '"',
                             }
                          )
        self.assertEqual(1, len(conditions))

        condition = conditions[0]
        self.assertEqual(EntityFilterCondition.EFC_FIELD,           condition.type)
        self.assertEqual(name,                                      condition.name)
        self.assertEqual({'operator': operator, 'values': [value]}, condition.decoded_value)


class DateFieldsConditionsFieldTestCase(FieldTestCase):
    def test_clean_invalid_data(self):
        clean = DateFieldsConditionsField(model=Contact).clean
        self.assertFieldValidationError(DateFieldsConditionsField, 'invalidfield', clean,
                                        '[{"field": {"name": "first_name", "type": "string__null"}, "range": {"type": "next_quarter", "start": "2011-5-12"}}]'
                                       )
        self.assertFieldValidationError(DateFieldsConditionsField, 'invalidformat', clean,
                                        '[{"field":  {"name": "birthday", "type": "date__null"}, "range":"not a dict"}]'
                                       )
        self.assertFieldValidationError(DateFieldsConditionsField, 'invaliddaterange', clean,
                                       '[{"field":  {"name": "birthday", "type": "date__null"}, "range": {"type":"unknow_range"}}]' #TODO: "start": '' ???
                                       )

        self.assertFieldValidationError(DateFieldsConditionsField, 'emptydates', clean,
                                       '[{"field":  {"name": "birthday", "type": "date__null"}, "range": {"type":""}}]'
                                       )
        self.assertFieldValidationError(DateFieldsConditionsField, 'emptydates', clean,
                                       '[{"field":  {"name": "birthday", "type": "date__null"}, "range": {"type":"", "start": "", "end": ""}}]'
                                       )

        try:   clean('[{"field": {"name": "created", "type": "date"}, "range": {"type": "", "start": "not a date"}}]')
        except ValidationError: pass
        else:  self.fail('No ValidationError')

        try:   clean('[{"field": {"name": "created", "type": "date"}, "range": {"type": "", "end": "2011-2-30"}}]') #30 february !!
        except ValidationError: pass
        else:  self.fail('No ValidationError')

    def test_ok01(self):
        field = DateFieldsConditionsField(model=Contact)
        type01 = 'current_year'
        name01 = 'created'
        type02 = 'next_quarter'
        name02 = 'birthday'
        conditions = field.clean('[{"field": {"name": "%(name01)s", "type": "date"}, "range": {"type": "%(type01)s"}},'
                                 ' {"field": {"name": "%(name02)s", "type": "date__null"}, "range": {"type": "%(type02)s"}}]' % {
                                        'type01': type01,
                                        'name01': name01,
                                        'type02': type02,
                                        'name02': name02,
                                    }
                                )
        self.assertEqual(2, len(conditions))

        condition = conditions[0]
        self.assertEqual(EntityFilterCondition.EFC_DATEFIELD, condition.type)
        self.assertEqual(name01,                              condition.name)
        self.assertEqual({'name': type01},                    condition.decoded_value)

        condition = conditions[1]
        self.assertEqual(EntityFilterCondition.EFC_DATEFIELD, condition.type)
        self.assertEqual(name02,                              condition.name)
        self.assertEqual({'name': type02},                    condition.decoded_value)

    def test_ok02(self):
        "Start/end"
        field = DateFieldsConditionsField(model=Contact)
        name01 = 'created'
        name02 = 'birthday'
        conditions = field.clean('[{"field": {"name": "%(name01)s", "type": "date"}, "range": {"type": "", "start": "2011-5-12"}},'
                                 ' {"field": {"name": "%(name02)s", "type": "date__null"}, "range": {"type": "", "end": "2012-6-13"}}]' % {
                                        'name01': name01,
                                        'name02': name02,
                                    }
                                )
        self.assertEqual(2, len(conditions))

        condition = conditions[0]
        self.assertEqual(EntityFilterCondition.EFC_DATEFIELD,              condition.type)
        self.assertEqual(name01,                                           condition.name)
        self.assertEqual({'start': {'year': 2011, 'month': 5, 'day': 12}}, condition.decoded_value)

        condition = conditions[1]
        self.assertEqual(EntityFilterCondition.EFC_DATEFIELD,            condition.type)
        self.assertEqual(name02,                                         condition.name)
        self.assertEqual({'end': {'year': 2012, 'month': 6, 'day': 13}}, condition.decoded_value)

    def test_ok03(self):
        "Start + end"
        clean = DateFieldsConditionsField(model=Contact).clean
        name = 'modified'
        conditions = clean('[{"field": {"name": "%s", "type": "date"}, "range": {"type": "", "start": "2010-3-24", "end": "2011-7-25"}}]' % name)
        self.assertEqual(1, len(conditions))

        condition = conditions[0]
        self.assertEqual(EntityFilterCondition.EFC_DATEFIELD, condition.type)
        self.assertEqual(name,                                condition.name)
        self.assertEqual({'start': {'year': 2010, 'month': 3, 'day': 24}, 'end': {'year': 2011, 'month': 7, 'day': 25}},
                         condition.decoded_value
                        )

    def test_empty(self):
        clean = DateFieldsConditionsField(model=Contact).clean
        conditions = clean('[{"field": {"name": "birthday", "type": "date__null"}, "range": {"type": "empty", "start": "", "end": ""}},'
                           ' {"field": {"name": "modified", "type": "date__null"}, "range": {"type": "not_empty", "start": "", "end": ""}}]')
        self.assertEqual(2, len(conditions))

        condition = conditions[0]
        self.assertEqual(EntityFilterCondition.EFC_DATEFIELD, condition.type)
        self.assertEqual('birthday',                          condition.name)
        self.assertEqual({'name': 'empty'},                   condition.decoded_value)

        condition = conditions[1]
        self.assertEqual(EntityFilterCondition.EFC_DATEFIELD, condition.type)
        self.assertEqual('modified',                          condition.name)
        self.assertEqual({'name': 'not_empty'},               condition.decoded_value)


class CustomFieldsConditionsFieldTestCase(FieldTestCase):
    CONDITION_FIELD_JSON_FMT = '[{"field": {"id": "%(field)s"}, "operator": {"id": "%(operator)s"}, "value": %(value)s}]'

    def setUp(self):
        ct = ContentType.objects.get_for_model(Contact)
        self.cfield_int = CustomField.objects.create(name='Size', content_type=ct, field_type=CustomField.INT)
        self.cfield_bool = CustomField.objects.create(name='Valid', content_type=ct, field_type=CustomField.BOOL)
        self.cfield_str = CustomField.objects.create(name='Name', content_type=ct, field_type=CustomField.STR)
        self.cfield_date = CustomField.objects.create(name='Date', content_type=ct, field_type=CustomField.DATETIME)
        self.cfield_float = CustomField.objects.create(name='Number', content_type=ct, field_type=CustomField.FLOAT)

        self.cfield_enum = CustomField.objects.create(name='Enum', content_type=ct, field_type=CustomField.ENUM)
        create_evalue = CustomFieldEnumValue.objects.create
        self.cfield_enum_A = create_evalue(custom_field=self.cfield_enum, value='A')
        create_evalue(custom_field=self.cfield_enum, value='B')
        create_evalue(custom_field=self.cfield_enum, value='C')

    def test_frompython_custom_int(self):
        field = CustomFieldsConditionsField(model=Contact)
        condition = EntityFilterCondition.build_4_customfield(self.cfield_int, EntityFilterCondition.EQUALS, 150);
        data = field._value_to_jsonifiable([condition])

        self.assertEqual([{'field': {'id': self.cfield_int.id,
                                      'type': 'number'},
                            'operator': {'id': EntityFilterCondition.EQUALS,
                                         'types': ' '.join(EntityFilterCondition._OPERATOR_MAP[EntityFilterCondition.EQUALS].allowed_fieldtypes)
                                        },
                            'value': 150
                           }
                         ], data)

    def test_frompython_custom_string(self):
        field = CustomFieldsConditionsField(model=Contact)
        condition = EntityFilterCondition.build_4_customfield(self.cfield_str, EntityFilterCondition.EQUALS, 'abc');
        data = field._value_to_jsonifiable([condition])

        self.assertEqual([{'field': {'id': self.cfield_str.id,
                                      'type': 'string'},
                            'operator': {'id': EntityFilterCondition.EQUALS,
                                         'types': ' '.join(EntityFilterCondition._OPERATOR_MAP[EntityFilterCondition.EQUALS].allowed_fieldtypes)
                                        },
                            'value': 'abc'
                          }
                         ], data)

    def test_frompython_custom_bool(self):
        field = CustomFieldsConditionsField(model=Contact)
        condition = EntityFilterCondition.build_4_customfield(self.cfield_bool, EntityFilterCondition.EQUALS, False);
        data = field._value_to_jsonifiable([condition])

        self.assertEqual([{'field': {'id': self.cfield_bool.id,
                                      'type': 'boolean'},
                            'operator': {'id': EntityFilterCondition.EQUALS,
                                         'types': ' '.join(EntityFilterCondition._OPERATOR_MAP[EntityFilterCondition.EQUALS].allowed_fieldtypes)
                                        },
                            'value': False
                          }
                         ], data)

    def test_frompython_custom_enum(self):
        field = CustomFieldsConditionsField(model=Contact)
        condition = EntityFilterCondition.build_4_customfield(self.cfield_enum, EntityFilterCondition.EQUALS, self.cfield_enum_A.id);
        data = field._value_to_jsonifiable([condition])

        self.assertEqual([{'field': {'id': self.cfield_enum.id,
                                      'type': 'enum'},
                            'operator': {'id': EntityFilterCondition.EQUALS,
                                         'types': ' '.join(EntityFilterCondition._OPERATOR_MAP[EntityFilterCondition.EQUALS].allowed_fieldtypes)
                                        },
                            'value': self.cfield_enum_A.id
                          }
                         ], data)

    def test_clean_invalid_data_format(self):
        field = CustomFieldsConditionsField(model=Contact)
        self.assertFieldValidationError(CustomFieldsConditionsField, 'invalidformat', field.clean,
                                        self.CONDITION_FIELD_JSON_FMT % {'field': "notanumber",
                                                                         'operator': EntityFilterCondition.EQUALS,
                                                                         'value': 170})

    def test_clean_invalid_field(self):
        field = CustomFieldsConditionsField(model=Contact)
        self.assertFieldValidationError(CustomFieldsConditionsField, 'invalidcustomfield', field.clean,
                                        self.CONDITION_FIELD_JSON_FMT % {'field': 2054,
                                                                         'operator': EntityFilterCondition.EQUALS,
                                                                         'value': 170})

        self.assertFieldValidationError(CustomFieldsConditionsField, 'invalidcustomfield', field.clean,
                                        '[{"operator": {"id": "%(operator)s"}, "value": %(value)s}]' % {
                                            'operator': EntityFilterCondition.EQUALS,
                                            'value': 170
                                        }
                                       )

    def test_clean_invalid_operator(self):
        field = CustomFieldsConditionsField(model=Contact)
        self.assertFieldValidationError(CustomFieldsConditionsField, 'invalidoperator', field.clean,
                                        self.CONDITION_FIELD_JSON_FMT % {'field': self.cfield_int.id,
                                                                         'operator': 121266,
                                                                         'value': 170})

        self.assertFieldValidationError(CustomFieldsConditionsField, 'invalidoperator', field.clean,
                                        '[{"field": {"id": "%(field)s"}, "value": %(value)s}]' % {
                                            'field': self.cfield_int.id,
                                            'value': 170
                                        }
                                       )

    def test_clean_missing_value(self):
        field = CustomFieldsConditionsField(model=Contact)
        self.assertFieldValidationError(CustomFieldsConditionsField, 'invalidvalue', field.clean,
                                        '[{"field": {"id": "%(field)s"}, "operator": {"id": "%(operator)s"}}]' % {
                                             'field': self.cfield_int.id,
                                             'operator': EntityFilterCondition.EQUALS,
                                        }
                                       )

    def test_clean_integer(self):
        clean = CustomFieldsConditionsField(model=Contact).clean
        operator = EntityFilterCondition.EQUALS
        value = 180
        conditions = clean(self.CONDITION_FIELD_JSON_FMT % {
                                                            'field':   self.cfield_int.id,
                                                            'operator': operator,
                                                            'value':    value,
                                                           }
                          )
        self.assertEqual(1, len(conditions))

        condition = conditions[0]
        self.assertEqual(EntityFilterCondition.EFC_CUSTOMFIELD, condition.type)
        self.assertEqual(str(self.cfield_int.id),             condition.name)
        self.assertEqual({'operator': operator, 'rname': 'customfieldinteger', 'value': unicode(value)},
                         condition.decoded_value
                        )

    def test_clean_empty_string(self):
        clean = CustomFieldsConditionsField(model=Contact).clean
        operator = EntityFilterCondition.EQUALS
        conditions = clean(self.CONDITION_FIELD_JSON_FMT % {
                                                            'field':   self.cfield_str.id,
                                                            'operator': operator,
                                                            'value':    '""',
                                                           }
                          )
        self.assertEqual(1, len(conditions))

        condition = conditions[0]
        self.assertEqual(EntityFilterCondition.EFC_CUSTOMFIELD, condition.type)
        self.assertEqual(str(self.cfield_str.id),               condition.name)
        self.assertEqual({'operator': operator, 'rname': 'customfieldstring', 'value': u''},
                         condition.decoded_value
                        )

    def test_customfield_choicetype(self):
        """custom field choice types"""
        self.autodiscover()
        #self.populate('persons')

        field_choicetype = CustomFieldConditionWidget.customfield_choicetype

        self.assertEqual(field_choicetype(self.cfield_enum), 'enum__null')
        self.assertEqual(field_choicetype(self.cfield_date), 'date__null')
        self.assertEqual(field_choicetype(self.cfield_bool),  'boolean__null')
        self.assertEqual(field_choicetype(self.cfield_int),   'number__null')
        self.assertEqual(field_choicetype(self.cfield_float), 'number__null')


class DateCustomFieldsConditionsFieldTestCase(FieldTestCase):
    def setUp(self):
        ct = ContentType.objects.get_for_model(Contact)
        self.cfield01 = CustomField.objects.create(name='Day', content_type=ct, field_type=CustomField.DATETIME)
        self.cfield02 = CustomField.objects.create(name='First flight', content_type=ct, field_type=CustomField.DATETIME)

    def test_clean_invalid_data(self):
        clean = DateCustomFieldsConditionsField(model=Contact).clean

        self.assertFieldValidationError(DateCustomFieldsConditionsField, 'invalidcustomfield', clean,
                                        '[{"field": "2054", "range": {"type": "current_year"}}]'
                                       )
        self.assertFieldValidationError(DateCustomFieldsConditionsField, 'invalidformat', clean,
                                        '[{"field": "%s", "range": "not a dict"}]' % self.cfield01.id
                                       )
        self.assertFieldValidationError(DateCustomFieldsConditionsField, 'invaliddaterange', clean,
                                       '[{"field": "%s", "range": {"type":"unknow_range"}}]' % self.cfield01.id
                                       )
        self.assertFieldValidationError(DateCustomFieldsConditionsField, 'emptydates', clean,
                                       '[{"field": "%s", "range": {"type":""}}]' % self.cfield01.id
                                       )
        self.assertFieldValidationError(DateCustomFieldsConditionsField, 'emptydates', clean,
                                       '[{"field": "%s", "range": {"type":"", "start": "", "end": ""}}]' % self.cfield01.id
                                       )

    def test_ok01(self):
        field = DateCustomFieldsConditionsField(model=Contact)
        rtype  = 'current_year'
        conditions = field.clean('[{"field": "%(cfield01)s", "range": {"type": "%(type)s"}},'
                                 ' {"field": "%(cfield02)s", "range": {"type": "", "start": "2011-5-12"}},'
                                 ' {"field": "%(cfield01)s", "range": {"type": "", "end": "2012-6-13"}},'
                                 ' {"field": "%(cfield02)s", "range": {"type": "", "start": "2011-5-12", "end": "2012-6-13"}}]' % {
                                        'type':     rtype,
                                        'cfield01': self.cfield01.id,
                                        'cfield02': self.cfield02.id,
                                    }
                                )
        self.assertEqual(4, len(conditions))

        condition = conditions[0]
        self.assertEqual(EntityFilterCondition.EFC_DATECUSTOMFIELD, condition.type)
        self.assertEqual(str(self.cfield01.id),                     condition.name)
        self.assertEqual({'rname': 'customfielddatetime', 'name': rtype}, condition.decoded_value)

        condition = conditions[1]
        self.assertEqual(EntityFilterCondition.EFC_DATECUSTOMFIELD, condition.type)
        self.assertEqual(str(self.cfield02.id),                     condition.name)
        self.assertEqual({'rname': 'customfielddatetime', 'start': {'year': 2011, 'month': 5, 'day': 12}},
                         condition.decoded_value
                        )

        condition = conditions[2]
        self.assertEqual(EntityFilterCondition.EFC_DATECUSTOMFIELD, condition.type)
        self.assertEqual(str(self.cfield01.id),                     condition.name)
        self.assertEqual({'rname': 'customfielddatetime', 'end': {'year': 2012, 'month': 6, 'day': 13}},
                         condition.decoded_value
                        )

        condition = conditions[3]
        self.assertEqual(EntityFilterCondition.EFC_DATECUSTOMFIELD, condition.type)
        self.assertEqual(str(self.cfield02.id),                     condition.name)
        self.assertEqual({'rname': 'customfielddatetime',
                          'start': {'year': 2011, 'month': 5, 'day': 12},
                          'end':   {'year': 2012, 'month': 6, 'day': 13},
                         },
                         condition.decoded_value
                        )

    def test_empty(self):
        field = DateCustomFieldsConditionsField(model=Contact)
        conditions = field.clean('[{"field": "%(cfield01)s", "range": {"type": "empty"}},'
                                 ' {"field": "%(cfield02)s", "range": {"type": "not_empty"}}]' % {
                                        'cfield01': self.cfield01.id,
                                        'cfield02': self.cfield02.id,
                                    }
                                )
        self.assertEqual(2, len(conditions))

        condition = conditions[0]
        self.assertEqual(EntityFilterCondition.EFC_DATECUSTOMFIELD, condition.type)
        self.assertEqual(str(self.cfield01.id),                     condition.name)
        self.assertEqual({'rname': 'customfielddatetime', 'name': 'empty'}, condition.decoded_value)

        condition = conditions[1]
        self.assertEqual(EntityFilterCondition.EFC_DATECUSTOMFIELD, condition.type)
        self.assertEqual(str(self.cfield02.id),                     condition.name)
        self.assertEqual({'rname': 'customfielddatetime', 'name': 'not_empty'},
                         condition.decoded_value
                        )


class PropertiesConditionsFieldTestCase(FieldTestCase):
    def setUp(self):
        self.ptype01 = CremePropertyType.create('test-prop_active', 'Is active')
        self.ptype02 = CremePropertyType.create('test-prop_cute',   'Is cute', (Contact,))
        self.ptype03 = CremePropertyType.create('test-prop_evil',   'Is evil', (Organisation,))

    def test_clean_empty_required(self):
        clean = PropertiesConditionsField(required=True).clean
        self.assertFieldValidationError(PropertiesConditionsField, 'required', clean, None)
        self.assertFieldValidationError(PropertiesConditionsField, 'required', clean, "")
        self.assertFieldValidationError(PropertiesConditionsField, 'required', clean, "[]")

    def test_clean_empty_not_required(self):
        #try:
        with self.assertNoException():
            PropertiesConditionsField(required=False).clean(None)
        #except Exception, e:
            #self.fail(str(e))

    def test_clean_invalid_data_type(self):
        clean = PropertiesConditionsField(model=Contact).clean
        self.assertFieldValidationError(PropertiesConditionsField, 'invalidtype', clean, '"this is a string"')
        self.assertFieldValidationError(PropertiesConditionsField, 'invalidtype', clean, '"{}"')
        self.assertFieldValidationError(PropertiesConditionsField, 'invalidtype', clean, '{"foobar":{"ptype": "test-foobar", "has": true}}')

#    def test_clean_invalid_data(self):
#        clean = PropertiesConditionsField(model=Contact).clean
#        self.assertFieldValidationError(PropertiesConditionsField, 'invalidformat', clean, '[{"ptype":"%s"}]' % self.ptype01.id)
#        self.assertFieldValidationError(PropertiesConditionsField, 'invalidformat', clean, '[{"has":"true"}]')
        #self.assertFieldValidationError(PropertiesConditionsField, 'invalidformat', clean, '[{"ptype":"%s","has":"not a boolean"}]' % self.ptype02.id)

    def test_clean_incomplete_data_required(self):
        clean = PropertiesConditionsField(model=Contact).clean
        self.assertFieldValidationError(PropertiesConditionsField, 'required', clean, '[{"ptype": "%s"}]' % self.ptype01.id)
        self.assertFieldValidationError(PropertiesConditionsField, 'required', clean, '[{"has": true}]')

    def test_unknown_ptype(self):
        self.assertFieldValidationError(PropertiesConditionsField, 'invalidptype',
                                        PropertiesConditionsField(model=Contact).clean,
                                        '[{"ptype": "%s", "has": true}]' % self.ptype03.id
                                       )

    def test_ok(self):
        field = PropertiesConditionsField(model=Contact)
        conditions = field.clean('[{"ptype": "%s", "has": true}, {"ptype": "%s", "has": false}]' % (self.ptype01.id, self.ptype02.id))
        self.assertEqual(2, len(conditions))

        condition = conditions[0]
        self.assertEqual(EntityFilterCondition.EFC_PROPERTY, condition.type)
        self.assertEqual(self.ptype01.id,                    condition.name)
        self.assertIs(condition.decoded_value, True)

        condition = conditions[1]
        self.assertEqual(EntityFilterCondition.EFC_PROPERTY, condition.type)
        self.assertEqual(self.ptype02.id,                    condition.name)
        self.assertIs(condition.decoded_value, False)


class RelationsConditionsFieldTestCase(FieldTestCase):
    def setUp(self):
        create = RelationType.create
        self.rtype01, self.rtype02 = create(('test-subject_love', u'Is loving', (Contact,)),
                                            ('test-object_love',  u'Is loved by')
                                           )
        self.rtype03, self.srtype04 = create(('test-subject_belong', u'(orga) belongs to (orga)', (Organisation,)),
                                             ('test-object_belong',  u'(orga) has (orga)',        (Organisation,))
                                            )

    def test_clean_empty_required(self):
        clean = RelationsConditionsField(required=True).clean
        self.assertFieldValidationError(RelationsConditionsField, 'required', clean, None)
        self.assertFieldValidationError(RelationsConditionsField, 'required', clean, "")
        self.assertFieldValidationError(RelationsConditionsField, 'required', clean, "[]")

    def test_clean_empty_not_required(self):
        #try:
        with self.assertNoException():
            RelationsConditionsField(required=False).clean(None)
        #except Exception, e:
            #self.fail(str(e))

    def test_clean_invalid_data_type(self):
        clean = RelationsConditionsField(model=Contact).clean
        self.assertFieldValidationError(RelationsConditionsField, 'invalidtype', clean, '"this is a string"')
        self.assertFieldValidationError(RelationsConditionsField, 'invalidtype', clean, '"{}"')
        self.assertFieldValidationError(RelationsConditionsField, 'invalidtype', clean, '{"foobar": {"rtype": "test-foobar", "has": true}}')

    def test_clean_invalid_data(self):
        clean = RelationsConditionsField(model=Contact).clean
        ct = ContentType.objects.get_for_model(Contact)
        self.assertFieldValidationError(RelationsConditionsField, 'invalidformat', clean, '[{"rtype": "%s", "has": true, "ctype": "not an int"}]' % self.rtype01.id)
        self.assertFieldValidationError(RelationsConditionsField, 'invalidformat', clean, '[{"rtype": "%s", "has": true, "ctype": %d, "entity": "not an int"}]' % (self.rtype01.id, ct.id))

    def test_clean_incomplete_data_required(self):
        clean = RelationsConditionsField(model=Contact).clean
        self.assertFieldValidationError(RelationsConditionsField, 'required', clean, '[{"rtype": "%s"}]' % self.rtype01.id)
        self.assertFieldValidationError(RelationsConditionsField, 'required', clean, '[{"has": true}]')
        self.assertFieldValidationError(RelationsConditionsField, 'required', clean, '[{"rtype": "%s", "has": "not a boolean"}]' % self.rtype01.id)

    def test_unknown_ct(self):
        clean = RelationsConditionsField(model=Contact).clean
        self.assertFieldValidationError(RelationsConditionsField, 'invalidct', clean, '[{"rtype": "%s", "has": true, "ctype": 2121545}]' % self.rtype01.id)

    def test_unknown_entity(self):
        clean = RelationsConditionsField(model=Contact).clean
        self.assertFieldValidationError(RelationsConditionsField, 'invalidentity', clean,
                                        '[{"rtype": "%s", "has": true, "ctype": 1, "entity": 2121545}]' % self.rtype01.id
                                       )

    def test_ok01(self):
        "No ct, no object entity"
        field = RelationsConditionsField(model=Contact)
        conditions = field.clean('[{"rtype": "%s", "has": true,  "ctype": 0, "entity": null},'
                                 ' {"rtype": "%s", "has": false, "ctype": 0, "entity": null}]' % (
                                    self.rtype01.id, self.rtype02.id)
                                )
        self.assertEqual(2, len(conditions))

        condition = conditions[0]
        self.assertEqual(EntityFilterCondition.EFC_RELATION, condition.type)
        self.assertEqual(self.rtype01.id,                    condition.name)
        self.assertEqual({'has': True},                      condition.decoded_value)

        condition = conditions[1]
        self.assertEqual(EntityFilterCondition.EFC_RELATION, condition.type)
        self.assertEqual(self.rtype02.id,                    condition.name)
        self.assertEqual({'has': False},                     condition.decoded_value)

    def test_ok02(self):
        "Wanted ct"
        field = RelationsConditionsField(model=Contact)
        ct = ContentType.objects.get_for_model(Contact)
        conditions = field.clean('[{"rtype": "%(rtype01)s", "has": true,  "ctype": %(ct)s, "entity": null},'
                                 ' {"rtype": "%(rtype02)s", "has": false, "ctype": %(ct)s}]' % {
                                        'rtype01': self.rtype01.id,
                                        'rtype02': self.rtype02.id,
                                        'ct':      ct.id,
                                    }
                                )
        self.assertEqual(2, len(conditions))

        condition = conditions[0]
        self.assertEqual(EntityFilterCondition.EFC_RELATION, condition.type)
        self.assertEqual(self.rtype01.id,                    condition.name)
        self.assertEqual({'has': True, 'ct_id': ct.id},      condition.decoded_value)

        condition = conditions[1]
        self.assertEqual(EntityFilterCondition.EFC_RELATION, condition.type)
        self.assertEqual(self.rtype02.id,                    condition.name)
        self.assertEqual({'has': False, 'ct_id': ct.id},     condition.decoded_value)

    def test_ok03(self):
        "Wanted entity"
        self.login()

        naru = Contact.objects.create(user=self.user, first_name='Naru', last_name='Narusegawa')
        field = RelationsConditionsField(model=Contact)
        ct = ContentType.objects.get_for_model(Contact)
        conditions = field.clean('[{"rtype":"%(rtype)s", "has": true, "ctype": %(ct)s, "entity":"%(entity)s"}]' % {
                                        'rtype':  self.rtype01.id,
                                        'ct':     ct.id,
                                        'entity': naru.id,
                                    }
                                )
        self.assertEqual(1, len(conditions))

        condition = conditions[0]
        self.assertEqual(EntityFilterCondition.EFC_RELATION,  condition.type)
        self.assertEqual(self.rtype01.id,                     condition.name)
        self.assertEqual({'has': True, 'entity_id': naru.id}, condition.decoded_value)

    def test_ok04(self):
        "Wanted ct + wanted entity"
        self.login()

        ct = ContentType.objects.get_for_model(Contact)
        naru = Contact.objects.create(user=self.user, first_name='Naru', last_name='Narusegawa')
        field = RelationsConditionsField(model=Contact)
        conditions = field.clean('[{"rtype": "%(rtype01)s", "has": true,  "ctype": %(ct)s, "entity": null},'
                                 ' {"rtype": "%(rtype02)s", "has": false, "ctype": %(ct)s, "entity": "%(entity)s"}]' % {
                                        'rtype01': self.rtype01.id,
                                        'rtype02': self.rtype02.id,
                                        'ct':      ct.id,
                                        'entity':  naru.id,
                                    }
                                )
        self.assertEqual(2, len(conditions))

        condition = conditions[0]
        self.assertEqual(EntityFilterCondition.EFC_RELATION, condition.type)
        self.assertEqual(self.rtype01.id,                    condition.name)
        self.assertEqual({'has': True, 'ct_id': ct.id},      condition.decoded_value)

        condition = conditions[1]
        self.assertEqual(EntityFilterCondition.EFC_RELATION,   condition.type)
        self.assertEqual(self.rtype02.id,                      condition.name)
        self.assertEqual({'has': False, 'entity_id': naru.id}, condition.decoded_value)

    def test_ok05(self):
        "Wanted entity is deleted"
        self.login()

        naru  = Contact.objects.create(user=self.user, first_name='Naru', last_name='Narusegawa')
        efilter = EntityFilter.create(pk='test-filter01', name='Filter 01', model=Contact, is_custom=True,
                                      conditions=[EntityFilterCondition.build_4_relation(
                                                        rtype=self.rtype01, has=True, entity=naru,
                                                    ),
                                                 ],
                                     )
        field = RelationsConditionsField(model=Contact)

        jsondict = {"entity": naru.id, "has": "true", "ctype": naru.entity_type_id, "rtype": self.rtype01.id}
        self.assertEqual([jsondict], jsonloads(field.from_python(list(efilter.conditions.all()))))

        try:
            naru.delete()
        except Exception, e:
            self.fail('Problem with entity deletion:' + str(e))

        jsondict["entity"] = None
        jsondict["ctype"] = 0
        self.assertEqual([jsondict], jsonloads(field.from_python(list(efilter.conditions.all()))))


class RelationSubfiltersConditionsFieldTestCase(FieldTestCase):
    def setUp(self):
        create = RelationType.create
        self.rtype01, self.rtype02 = create(('test-subject_love', u'Is loving', (Contact,)),
                                            ('test-object_love',  u'Is loved by')
                                           )
        self.rtype03, self.srtype04 = create(('test-subject_belong', u'(orga) belongs to (orga)', (Organisation,)),
                                             ('test-object_belong',  u'(orga) has (orga)',        (Organisation,))
                                            )

        self.sub_efilter01 = EntityFilter.create(pk='test-filter01', name='Filter 01', model=Contact,      is_custom=True)
        self.sub_efilter02 = EntityFilter.create(pk='test-filter02', name='Filter 02', model=Organisation, is_custom=True)

    def test_clean_empty_required(self):
        clean = RelationSubfiltersConditionsField(required=True).clean
        self.assertFieldValidationError(RelationSubfiltersConditionsField, 'required', clean, None)
        self.assertFieldValidationError(RelationSubfiltersConditionsField, 'required', clean, "")
        self.assertFieldValidationError(RelationSubfiltersConditionsField, 'required', clean, "[]")

#    def test_clean_invalid_data(self):
#        clean = RelationSubfiltersConditionsField(model=Contact).clean
#        self.assertFieldValidationError(RelationSubfiltersConditionsField, 'invalidformat', clean, '[{"rtype":"%s"}]' % self.rtype01.id)
#        self.assertFieldValidationError(RelationSubfiltersConditionsField, 'invalidformat', clean, '[{"has":"true"}]')

    def test_clean_incomplete_data_required(self):
        clean = RelationSubfiltersConditionsField(model=Contact).clean
        self.assertFieldValidationError(RelationSubfiltersConditionsField, 'required', clean, '[{"rtype": "%s"}]' % self.rtype01.id)
        self.assertFieldValidationError(RelationSubfiltersConditionsField, 'required', clean, '[{"has": true}]')

    def test_unknown_filter(self):
        user = self.login()
        field = RelationSubfiltersConditionsField(model=Contact)
        field.user = user
        self.assertFieldValidationError(RelationSubfiltersConditionsField, 'invalidfilter', field.clean,
                                        '[{"rtype": "%(rtype)s", "has": false, "ctype": %(ct)s, "filter": "%(filter)s"}]' % {
                                                'rtype':  self.rtype01.id,
                                                'ct':     ContentType.objects.get_for_model(Contact).id,
                                                'filter': 3213213543,
                                            }
                                       )

    def test_ok(self):
        user = self.login()

        get_ct = ContentType.objects.get_for_model
        ct_contact = get_ct(Contact)
        ct_orga    = get_ct(Organisation)

        field = RelationSubfiltersConditionsField(model=Contact)
        field.user = user

        conditions = field.clean('[{"rtype": "%(rtype01)s", "has": true,  "ctype": %(ct_contact)s, "filter":"%(filter01)s"},'
                                 ' {"rtype": "%(rtype02)s", "has": false, "ctype": %(ct_orga)s,    "filter":"%(filter02)s"}]' % {
                                        'rtype01':    self.rtype01.id,
                                        'rtype02':    self.rtype02.id,
                                        'ct_contact': ct_contact.id,
                                        'ct_orga':    ct_orga.id,
                                        'filter01':   self.sub_efilter01.id,
                                        'filter02':   self.sub_efilter02.id,
                                    }
                                )
        self.assertEqual(2, len(conditions))

        condition = conditions[0]
        self.assertEqual(EntityFilterCondition.EFC_RELATION_SUBFILTER,      condition.type)
        self.assertEqual(self.rtype01.id,                                   condition.name)
        self.assertEqual({'has': True, 'filter_id': self.sub_efilter01.id}, condition.decoded_value)

        condition = conditions[1]
        self.assertEqual(EntityFilterCondition.EFC_RELATION_SUBFILTER,       condition.type)
        self.assertEqual(self.rtype02.id,                                    condition.name)
        self.assertEqual({'has': False, 'filter_id': self.sub_efilter02.id}, condition.decoded_value)
