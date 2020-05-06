# -*- coding: utf-8 -*-

try:
    from functools import partial

    from django.contrib.contenttypes.models import ContentType
    from django.utils.translation import gettext as _

    from creme.creme_core.core.entity_cell import EntityCellRegularField
    from creme.creme_core.models import (
        CustomField,
        FieldsConfig,
        FakeOrganisation, FakeContact
    )
    from creme.creme_core.tests.forms.base import FieldTestCase

    from creme.reports.forms.report import (
        _EntityCellAggregate, _EntityCellCustomAggregate,
        ReportHandsField,
    )
except Exception as e:
    print('Error in <{}>: {}'.format(__name__, e))


# TODO: complete
#   - excluded FK to CremeEntity
#   - widget.related_entities
#   ...
class ReportHandsFieldTestCase(FieldTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ct_orga = ContentType.objects.get_for_model(FakeOrganisation)

    def test_clean_empty_required(self):
        clean = ReportHandsField(required=True, content_type=self.ct_orga).clean
        self.assertFieldValidationError(ReportHandsField, 'required', clean, None)
        self.assertFieldValidationError(ReportHandsField, 'required', clean, '')

    def test_clean_empty_not_required(self):
        field = ReportHandsField(required=False, content_type=self.ct_orga)

        with self.assertNoException():
            value = field.clean(None)

        self.assertEqual([], value)

    def test_clean_invalid_choice(self):
        field = ReportHandsField(content_type=self.ct_orga)
        self.assertFieldValidationError(
            ReportHandsField, 'invalid', field.clean,
            'regular_field-fname,regular_field-unknown',
        )

    def test_choices_regularfields02(self):
        field = ReportHandsField(content_type=self.ct_orga)
        self.assertListEqual([], field.non_hiddable_cells)

        widget = field.widget
        choices = widget.model_fields
        self.assertInChoices(
            value='regular_field-name',
            label=_('Name'),
            choices=choices,
        )
        self.assertInChoices(
            value='regular_field-sector',
            label=_('Sector'),
            choices=choices,
        )
        self.assertInChoices(
            value='regular_field-sector__title',
            label=_('Title'),
            choices=widget.model_subfields['regular_field-sector'],
        )

        cells = field.clean('regular_field-name')
        self.assertEqual(1, len(cells))

        cell = cells[0]
        self.assertIsInstance(cell, EntityCellRegularField)
        self.assertEqual(FakeOrganisation, cell.model)
        self.assertEqual('name',           cell.value)

    def test_regular_aggregates01(self):
        field = ReportHandsField()
        widget = field.widget
        self.assertListEqual([], [*widget.regular_aggregates])

        field.content_type = self.ct_orga
        fvname = _('Capital')
        fmt = '{} - {}'.format
        self.assertListEqual(
            [
                ('regular_aggregate-capital__avg', fmt(_('Average'), fvname)),
                ('regular_aggregate-capital__min', fmt(_('Minimum'), fvname)),
                ('regular_aggregate-capital__max', fmt(_('Maximum'), fvname)),
                ('regular_aggregate-capital__sum', fmt(_('Sum'), fvname)),
            ],
            [*widget.regular_aggregates]
        )

        cells = field.clean('regular_aggregate-capital__avg')
        self.assertEqual(1, len(cells))

        cell = cells[0]
        self.assertIsInstance(cell, _EntityCellAggregate)
        self.assertEqual(FakeOrganisation, cell.model)
        self.assertEqual('capital__avg',   cell.value)

    def test_regular_aggregates02(self):
        "Field is hidden."
        field_name = 'capital'
        FieldsConfig.objects.create(
            content_type=FakeOrganisation,
            descriptions=[(field_name, {FieldsConfig.HIDDEN: True})],
        )

        field = ReportHandsField(content_type=self.ct_orga)
        self.assertListEqual([], [*field.widget.regular_aggregates])
        self.assertFieldValidationError(
            ReportHandsField, 'invalid', field.clean,
            'regular_aggregate-capital__avg',
        )

    def test_regular_aggregates03(self):
        "Field is hidden but already used => it is still proposed."
        hidden_fname = 'capital'
        FieldsConfig.objects.create(
            content_type=FakeOrganisation,
            descriptions=[(hidden_fname, {FieldsConfig.HIDDEN: True})],
        )

        field = ReportHandsField()
        field.non_hiddable_cells = [
            _EntityCellAggregate(FakeOrganisation, '{}__avg'.format(hidden_fname))
        ]
        # BEWARE: must be set after 'non_hiddable_cells' (fixed in Creme2.2)
        field.content_type = self.ct_orga

        self.assertListEqual(
            [('regular_aggregate-capital__avg', '{} - {}'.format(_('Average'), _('Capital')))],
            [*field.widget.regular_aggregates]
        )

        cells = field.clean('regular_aggregate-capital__avg')
        self.assertEqual(1, len(cells))

        cell = cells[0]
        self.assertIsInstance(cell, _EntityCellAggregate)
        self.assertEqual(FakeOrganisation, cell.model)
        self.assertEqual('capital__avg',   cell.value)

    def test_custom_aggregates(self):
        create_cf = partial(
            CustomField.objects.create,
            content_type=self.ct_orga,
        )
        cf1 = create_cf(field_type=CustomField.INT, name='Rank')
        create_cf(field_type=CustomField.STR, name='Tag')
        create_cf(
            field_type=CustomField.BOOL, name='Operational?',
            content_type=FakeContact,
        )

        field = ReportHandsField()
        widget = field.widget
        self.assertListEqual([], [*widget.custom_aggregates])

        field.content_type = self.ct_orga
        fmt = '{} - {}'.format
        self.assertListEqual(
            [
                ('custom_aggregate-{}__avg'.format(cf1.id), fmt(_('Average'), cf1.name)),
                ('custom_aggregate-{}__min'.format(cf1.id), fmt(_('Minimum'), cf1.name)),
                ('custom_aggregate-{}__max'.format(cf1.id), fmt(_('Maximum'), cf1.name)),
                ('custom_aggregate-{}__sum'.format(cf1.id), fmt(_('Sum'), cf1.name)),
            ],
            [*widget.custom_aggregates]
        )

        cells = field.clean('custom_aggregate-{}__avg'.format(cf1.id))
        self.assertEqual(1, len(cells))

        cell = cells[0]
        self.assertIsInstance(cell, _EntityCellCustomAggregate)
        self.assertEqual(FakeOrganisation, cell.model)
        self.assertEqual('{}__avg'.format(cf1.id), cell.value)
