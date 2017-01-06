# -*- coding: utf-8 -*-

try:
    from django.core.exceptions import ValidationError
    from django.contrib.contenttypes.models import ContentType
    from django.forms import IntegerField, ChoiceField
    from django.utils.timezone import now
    from django.utils.translation import ugettext as _

    from .base import FieldTestCase
    from ..fake_models import FakeContact as Contact, FakeOrganisation as Organisation
    from creme.creme_core.forms.fields import (DatePeriodField, DateRangeField,
        DurationField, ColorField, ChoiceOrCharField,
        OptionalChoiceField,
        CTypeChoiceField, EntityCTypeChoiceField,
        MultiCTypeChoiceField, MultiEntityCTypeChoiceField)
    from creme.creme_core.models import RelationType, CremePropertyType, Currency
    from creme.creme_core.utils.date_period import DatePeriod
    from creme.creme_core.utils.date_range import DateRange, CustomRange, CurrentYearRange
except Exception as e:
    print('Error in <%s>: %s' % (__name__, e))


class DatePeriodFieldTestCase(FieldTestCase):
    def test_ok01(self):
        "Days"
        period = DatePeriodField().clean(['days', '3'])
        self.assertIsInstance(period, DatePeriod)

        create_dt = self.create_datetime
        self.assertEqual(create_dt(year=2014, month=7, day=5, hour=22, minute=9),
                         create_dt(year=2014, month=7, day=2, hour=22, minute=9)
                         + period.as_timedelta()
                        )

    def test_ok02(self):
        "Minutes"
        period = DatePeriodField().clean(['minutes', '5'])
        self.assertIsInstance(period, DatePeriod)

        create_dt = self.create_datetime
        self.assertEqual(create_dt(year=2014, month=7, day=2, hour=22, minute=14),
                         create_dt(year=2014, month=7, day=2, hour=22, minute=9)
                         + period.as_timedelta()
                        )

    def test_required(self):
        clean = DatePeriodField().clean
        self.assertFieldValidationError(DatePeriodField, 'required', clean, ['', ''])
        self.assertFieldValidationError(DatePeriodField, 'required', clean, None)

    def test_not_required(self):
        clean = DatePeriodField(required=False).clean
        self.assertIsNone(clean(['', '']))
        self.assertIsNone(clean(['']))
        self.assertIsNone(clean([]))
        self.assertIsNone(clean(['days', '']))
        self.assertIsNone(clean(['days']))
        self.assertIsNone(clean(['', 2]))

    def test_empty(self):
        self.assertIsNone(DatePeriodField(required=False).clean(None))

    def test_invalid(self):
        clean = DatePeriodField().clean
        self.assertFieldValidationError(IntegerField, 'invalid', clean, ['years', 'notint'])

        name = 'unknownperiod'
        self.assertFieldValidationError(ChoiceField, 'invalid_choice', clean,
                                        [name, '2'], message_args={'value': name},
                                       )

    def test_choices(self):
        clean = DatePeriodField(choices=('months',)).clean
        period = clean(['months', '5'])
        self.assertIsInstance(period, DatePeriod)

        name = 'years'
        self.assertFieldValidationError(ChoiceField, 'invalid_choice', clean,
                                        [name, '2'], message_args={'value': name},
                                       )

    def test_notnull(self):
        with self.assertRaises(ValidationError) as cm:
            DatePeriodField().clean(['days', '0'])

        self.assertEqual([_('Ensure this value is greater than or equal to %(limit_value)s.') % {
                                'limit_value': 1
                            },
                         ],
                         cm.exception.messages
                        )


class DateRangeFieldTestCase(FieldTestCase):
    def test_clean_empty_customized(self):
        clean = DateRangeField().clean
        self.assertFieldValidationError(DateRangeField, 'required', clean, ['', '', ''])
        self.assertFieldValidationError(DateRangeField, 'required', clean, None)

    def test_start_before_end(self):
        self.assertFieldValidationError(DateRangeField, 'customized_invalid',
                                        DateRangeField().clean, [u"", u"2011-05-16", u"2011-05-15"]
                                       )

    def test_ok01(self):
        drange = DateRangeField().clean(['', '2013-05-29', '2013-06-16'])
        dt = self.create_datetime
        self.assertIsInstance(drange, DateRange)
        self.assertIsInstance(drange, CustomRange)
        self.assertEqual((dt(year=2013, month=5, day=29, hour=0,  minute=0,  second=0),
                          dt(year=2013, month=6, day=16, hour=23, minute=59, second=59),
                         ),
                         drange.get_dates(now())
                        )

    def test_ok02(self):
        drange = DateRangeField().clean([CurrentYearRange.name, '', ''])
        dt = self.create_datetime
        self.assertIsInstance(drange, CurrentYearRange)
        self.assertEqual((dt(year=2013, month=1, day=1,   hour=0,  minute=0,  second=0),
                          dt(year=2013, month=12, day=31, hour=23, minute=59, second=59),
                         ),
                         drange.get_dates(dt(year=2013, month=5, day=29, hour=11))
                        )

    def test_ok03(self):
        drange = DateRangeField(required=False).clean(['', '', ''])
        self.assertIsNone(drange)


class ColorFieldTestCase(FieldTestCase):
    def test_empty01(self):
        clean = ColorField().clean
        self.assertFieldValidationError(ColorField, 'required', clean, None)
        self.assertFieldValidationError(ColorField, 'required', clean, '')
        self.assertFieldValidationError(ColorField, 'required', clean, [])

    def test_length01(self):
        clean = ColorField().clean
        self.assertFieldRaises(ValidationError, clean, '1')
        self.assertFieldRaises(ValidationError, clean, '12')
        self.assertFieldRaises(ValidationError, clean, '123')
        self.assertFieldRaises(ValidationError, clean, '1234')
        self.assertFieldRaises(ValidationError, clean, '12345')

    def test_invalid_value01(self):
        clean = ColorField().clean
        self.assertFieldValidationError(ColorField, 'invalid', clean, 'GGGGGG')
        self.assertFieldValidationError(ColorField, 'invalid', clean, '------')

    def test_ok01(self):
        clean = ColorField().clean
        self.assertEqual('AAAAAA', clean('AAAAAA'))
        self.assertEqual('AAAAAA', clean('aaaaaa'))
        self.assertEqual('123456', clean('123456'))
        self.assertEqual('123ABC', clean('123ABC'))
        self.assertEqual('123ABC', clean('123abc'))


class DurationFieldTestCase(FieldTestCase):
    def test_empty01(self):
        clean = DurationField().clean
        self.assertFieldValidationError(DurationField, 'required', clean, None)
        self.assertFieldValidationError(DurationField, 'required', clean, '')
        self.assertFieldValidationError(DurationField, 'required', clean, [])

    def test_invalid01(self):
        self.assertFieldValidationError(DurationField, 'invalid', DurationField().clean, [u'a', u'b', u'c'])

    def test_positive01(self):
        self.assertFieldValidationError(DurationField, 'min_value', DurationField().clean,
                                        [u'-1', u'-1', u'-1'], message_args={'limit_value': 0}
                                       )

    def test_ok01(self):
        clean = DurationField().clean
        self.assertEqual('10:2:0', clean([u'10', u'2', u'0']))
        self.assertEqual('10:2:0', clean([10, 2, 0]))


class OptionalChoiceFieldTestCase(FieldTestCase):
    _team = ['Naruto', 'Sakura', 'Sasuke', 'Kakashi']

    def test_ok_choice(self):
        field = OptionalChoiceField(choices=enumerate(self._team, start=1))
        self.assertEqual((True, '1'), field.clean([True, 1]))

    def test_not_required(self):
        field = OptionalChoiceField(choices=enumerate(self._team, start=1), required=False)
        expected = (False, None)
        self.assertEqual(expected, field.clean([False, '']))
        self.assertEqual(expected, field.clean([False, 1]))
        self.assertEqual(expected, field.clean([False, None]))
        self.assertEqual(expected, field.clean([False]))
        self.assertEqual(expected, field.clean([]))

    def test_required(self):
        clean = OptionalChoiceField(choices=enumerate(self._team, start=1), required=True).clean

        expected = (False, None)
        self.assertEqual(expected, clean([False, None]))
        self.assertEqual(expected, clean([False]))
        self.assertEqual(expected, clean([]))

        self.assertFieldValidationError(OptionalChoiceField, 'subfield_required', clean, [True, None])
        self.assertFieldValidationError(OptionalChoiceField, 'subfield_required', clean, [True])

    def test_invalid(self):
        field = OptionalChoiceField(choices=enumerate(self._team, start=1))

        with self.assertRaises(ValidationError) as cm:
            field.clean([False, 'invalid'])

        self.assertEqual([_('Select a valid choice. %(value)s is not one of the available choices.') % {
                                'value': 'invalid',
                            },
                         ],
                         cm.exception.messages
                        )


class ChoiceOrCharFieldTestCase(FieldTestCase):
    _team = ['Naruto', 'Sakura', 'Sasuke', 'Kakashi']

    def test_empty_required(self):
        clean = ChoiceOrCharField(choices=enumerate(self._team, start=1)).clean
        self.assertFieldValidationError(ChoiceOrCharField, 'required', clean, None)
        self.assertFieldValidationError(ChoiceOrCharField, 'required', clean, '')
        self.assertFieldValidationError(ChoiceOrCharField, 'required', clean, [])

    def test_empty_other(self):
        field = ChoiceOrCharField(choices=enumerate(self._team, start=1))
        self.assertFieldValidationError(ChoiceOrCharField, 'invalid_other', field.clean, [0, ''])

    def test_ok_choice(self):
        field = ChoiceOrCharField(choices=enumerate(self._team, start=1))
        self.assertEqual((1, 'Naruto'), field.clean([1, '']))

    def test_ok_other(self):
        field = ChoiceOrCharField(choices=enumerate(self._team, start=1))

        with self.assertNoException():
            choices = field.choices

        self.assertIn((0, _('Other')), choices)

        other = 'Shikamaru'
        self.assertEqual((0, other), field.clean([0, other]))

    def test_empty_ok(self):
        field = ChoiceOrCharField(choices=enumerate(self._team, start=1), required=False)

        with self.assertNoException():
            cleaned = field.clean(['', ''])

        self.assertEqual((None, None), cleaned)

    # TODO: set 'Other' label


class _CTypeChoiceFieldTestCase(FieldTestCase):
    @classmethod
    def setUpClass(cls):
        FieldTestCase.setUpClass()

        get_ct = ContentType.objects.get_for_model
        cls.ct1 = get_ct(RelationType)
        cls.ct2 = get_ct(CremePropertyType)
        cls.ct3 = get_ct(Currency)


class CTypeChoiceFieldTestCase(_CTypeChoiceFieldTestCase):
    def test_required(self):
        ct1 = self.ct1
        ct2 = self.ct2
        field = CTypeChoiceField(ctypes=[ct1, ct2])
        clean = field.clean

        self.assertEqual(sorted([(ct1.pk, unicode(ct1)),
                                 (ct2.pk, unicode(ct2)),
                                ], key=lambda ct: ct[1]),
                         list(field.widget.choices)
                        )

        self.assertEqual(ct1, clean(ct1.id))
        self.assertEqual(ct2, clean(ct2.id))
        self.assertFieldValidationError(CTypeChoiceField, 'required', clean, '')

    def test_not_required(self):
        ct1 = self.ct1
        ct2 = self.ct2
        field = CTypeChoiceField(ctypes=[ct1, ct2], required=False)
        clean = field.clean

        self.assertEqual([('', field.empty_label)] +
                         sorted([(ct1.pk, unicode(ct1)),
                                 (ct2.pk, unicode(ct2)),
                                ], key=lambda ct: ct[1]),
                         list(field.widget.choices)
                        )

        self.assertEqual(ct1, clean(ct1.id))
        self.assertEqual(ct2, clean(ct2.id))
        self.assertEqual(None, clean(''))

    def test_invalid(self):
        clean = CTypeChoiceField(ctypes=[self.ct1, self.ct2]).clean
        self.assertFieldValidationError(CTypeChoiceField, 'invalid_choice',
                                        clean, self.ct3.id,
                                       )


class _EntityCTypeChoiceFieldTestCase(FieldTestCase):
    @classmethod
    def setUpClass(cls):
        FieldTestCase.setUpClass()

        get_ct = ContentType.objects.get_for_model
        cls.ct1 = get_ct(Contact)
        cls.ct2 = get_ct(Organisation)
        cls.ct3 = get_ct(Currency)


class EntityCTypeChoiceFieldTestCase(_EntityCTypeChoiceFieldTestCase):
    def test_required(self):
        ct1 = self.ct1
        ct2 = self.ct2
        clean = EntityCTypeChoiceField().clean
        self.assertEqual(ct1, clean(ct1.id))
        self.assertEqual(ct2, clean(ct2.id))
        self.assertFieldValidationError(EntityCTypeChoiceField, 'required', clean, '')

    def test_not_required(self):
        ct1 = self.ct1
        ct2 = self.ct2
        clean = EntityCTypeChoiceField(required=False).clean
        self.assertEqual(ct1, clean(ct1.id))
        self.assertEqual(ct2, clean(ct2.id))
        self.assertEqual(None, clean(''))

    def test_invalid(self):
        self.assertFieldValidationError(EntityCTypeChoiceField, 'invalid_choice',
                                        EntityCTypeChoiceField().clean, self.ct3.id,
                                       )

    def test_ctypes01(self):
        "Constructor"
        ct1 = self.ct1

        with self.assertNumQueries(0):
            field = EntityCTypeChoiceField(ctypes=[ct1])

        clean = field.clean
        self.assertEqual(ct1, clean(ct1.id))
        self.assertFieldValidationError(EntityCTypeChoiceField,
                                        'invalid_choice', clean, self.ct2.id,
                                       )

    def test_ctypes02(self):
        "Setter"
        ct1 = self.ct1
        field = EntityCTypeChoiceField()
        field.ctypes = [ct1]

        clean = field.clean
        self.assertEqual(ct1, clean(ct1.id))
        self.assertFieldValidationError(EntityCTypeChoiceField,
                                        'invalid_choice', clean, self.ct2.id,
                                       )

    def test_ctypes03(self):
        "All accepted"
        ContentType.objects.clear_cache()

        with self.assertNumQueries(0):
            field = EntityCTypeChoiceField()

        ct1 = self.ct1
        self.assertEqual(ct1, field.clean(ct1.id))


class MultiCTypeChoiceFieldTestCase(_CTypeChoiceFieldTestCase):
    def test_required(self):
        ct1 = self.ct1
        ct2 = self.ct2
        field = MultiCTypeChoiceField(ctypes=[ct1, ct2])
        clean = field.clean

        self.assertEqual(sorted([(ct1.pk, unicode(ct1)),
                                 (ct2.pk, unicode(ct2)),
                                ], key=lambda ct: ct[1]),
                         [(choice.value, label) for choice, label in field.widget.choices])

        self.assertEqual([ct1], clean([ct1.id]))
        self.assertEqual([ct2], clean([ct2.id]))
        self.assertFieldValidationError(MultiCTypeChoiceField, 'required', clean, '')
        self.assertFieldValidationError(MultiCTypeChoiceField, 'required', clean, [])
        self.assertFieldValidationError(MultiCTypeChoiceField, 'required', clean, None)

    def test_not_required(self):
        ct1 = self.ct1
        ct2 = self.ct2
        field = MultiCTypeChoiceField(ctypes=[ct1, ct2], required=False)
        clean = field.clean

        self.assertEqual(sorted([(ct1.pk, unicode(ct1)),
                                 (ct2.pk, unicode(ct2)),
                                ], key=lambda ct: ct[1]),
                         [(choice.value, label) for choice, label in field.widget.choices])

        self.assertEqual([ct1], clean([ct1.id]))
        self.assertEqual([ct2], clean([ct2.id]))
        self.assertEqual([],    clean(''))
        self.assertEqual([],    clean([]))

    def test_invalid(self):
        ct1 = self.ct1
        clean = MultiCTypeChoiceField(ctypes=[ct1, self.ct2]).clean
        self.assertFieldValidationError(MultiCTypeChoiceField, 'invalid_choice',
                                        clean, [ct1.id, self.ct3.id],
                                       )
        self.assertFieldValidationError(MultiCTypeChoiceField, 'invalid_choice',
                                        clean, ['not an int'],
                                       )


class MultiEntityCTypeChoiceFieldTestCase(_EntityCTypeChoiceFieldTestCase):
    def test_required(self):
        ct1 = self.ct1
        ct2 = self.ct2

        ContentType.objects.clear_cache()

        with self.assertNumQueries(0):
            field = MultiEntityCTypeChoiceField()

        clean = field.clean
        self.assertEqual([ct1], clean([ct1.id]))
        self.assertEqual([ct2], clean([ct2.id]))
        self.assertFieldValidationError(MultiEntityCTypeChoiceField, 'required', clean, '')
        self.assertFieldValidationError(MultiEntityCTypeChoiceField, 'required', clean, [])
        self.assertFieldValidationError(MultiEntityCTypeChoiceField, 'required', clean, None)

    def test_not_required(self):
        ct1 = self.ct1
        ct2 = self.ct2
        clean = MultiEntityCTypeChoiceField(ctypes=[ct1, ct2], required=False).clean

        self.assertEqual([ct1], clean([ct1.id]))
        self.assertEqual([ct2], clean([ct2.id]))
        self.assertEqual([],    clean(''))
        self.assertEqual([],    clean([]))

    def test_invalid(self):
        clean = MultiEntityCTypeChoiceField().clean
        self.assertFieldValidationError(MultiEntityCTypeChoiceField, 'invalid_choice',
                                        clean, [self.ct1.id, self.ct3.id],
                                       )
        self.assertFieldValidationError(MultiEntityCTypeChoiceField, 'invalid_choice',
                                        clean, ['not an int'],
                                       )

    def test_ctypes(self):
        ct1 = self.ct1
        clean = MultiEntityCTypeChoiceField(ctypes=[ct1]).clean
        self.assertEqual([ct1], clean([ct1.id]))
        self.assertFieldValidationError(MultiEntityCTypeChoiceField,
                                        'invalid_choice', clean, [self.ct2.id],
                                       )
