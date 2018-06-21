# -*- coding: utf-8 -*-

try:
    from decimal import Decimal
    from functools import partial

    from django.urls import reverse
    from django.utils.translation import ugettext as _

    from creme.creme_core.models import Relation, Currency, FieldsConfig

    from creme.persons.tests.base import skipIfCustomOrganisation

    from ..models import CreditNoteStatus
    from ..constants import REL_SUB_CREDIT_NOTE_APPLIED
    from .base import (_BillingTestCase, skipIfCustomCreditNote,
            skipIfCustomProductLine, skipIfCustomInvoice,
            Organisation, CreditNote, ProductLine)
except Exception as e:
    print('Error in <{}>: {}'.format(__name__, e))


@skipIfCustomOrganisation
@skipIfCustomCreditNote
class CreditNoteTestCase(_BillingTestCase):
    def setUp(self):
        self.login()

    def _build_editcomment_url(self, credit_note):
        return reverse('billing__edit_cnote_comment', args=(credit_note.id,))

    def _build_deleterelated_url(self, credit_note, invoice):
        return reverse('billing__delete_related_cnote', args=(credit_note.id, invoice.id))

    def create_credit_note(self, name, source, target, currency=None, discount=Decimal(), user=None, status=None):
        user = user or self.user
        status = status or CreditNoteStatus.objects.all()[0]
        currency = currency or Currency.objects.all()[0]
        response = self.client.post(reverse('billing__create_cnote'), follow=True,
                                    data={'user':            user.id,
                                          'name':            name,
                                          'issuing_date':    '2010-9-7',
                                          'expiration_date': '2010-10-13',
                                          'status':          status.id,
                                          'currency':        currency.id,
                                          'discount':        discount,
                                          'source':          source.id,
                                          'target':          self.formfield_value_generic_entity(target),
                                         }
                                   )
        self.assertNoFormError(response)

        credit_note = self.get_object_or_fail(CreditNote, name=name)
        self.assertRedirects(response, credit_note.get_absolute_url())

        return credit_note

    def create_credit_note_n_orgas(self, name, user=None, status=None, **kwargs):
        user = user or self.user
        create_orga = partial(Organisation.objects.create, user=user)
        source = create_orga(name='Source Orga')
        target = create_orga(name='Target Orga')

        credit_note = self.create_credit_note(name, source, target, user=user, status=status, **kwargs)

        return credit_note, source, target

    def assertInvoiceTotalToPay(self, invoice, total):
        invoice = self.refresh(invoice)
        expected_total = Decimal(total)
        self.assertEqual(expected_total, invoice.total_no_vat)
        self.assertEqual(expected_total, invoice.total_vat)

    @skipIfCustomInvoice
    @skipIfCustomProductLine
    def test_createview01(self):
        "Credit note total < billing document total where the credit note is applied"
        self.assertGET200(reverse('billing__create_cnote'))

        invoice = self.create_invoice_n_orgas('Invoice0001', discount=0)[0]

        user = self.user
        create_line = partial(ProductLine.objects.create, user=user)
        create_line(related_document=invoice, on_the_fly_item='Otf1', unit_price=Decimal("100"))
        create_line(related_document=invoice, on_the_fly_item='Otf2', unit_price=Decimal("200"))

        credit_note = self.create_credit_note_n_orgas('Credit Note 001')[0]
        create_line(related_document=credit_note, on_the_fly_item='Otf3', unit_price=Decimal("299"))

        # TODO: the credit note must be valid : Status OK (not out of date or consumed),
        #                                       Target = Billing document's target
        #                                       currency = billing document's currency
        # These rules must be applied with q filter on list view before selection
        Relation.objects.create(object_entity=invoice, subject_entity=credit_note,
                                type_id=REL_SUB_CREDIT_NOTE_APPLIED, user=user,
                               )

        invoice = self.refresh(invoice)
        expected_total = Decimal('1')
        self.assertEqual(expected_total, invoice.total_no_vat)
        self.assertEqual(expected_total, invoice.total_vat)

    @skipIfCustomInvoice
    @skipIfCustomProductLine
    def test_createview02(self):
        "Credit note total > document billing total where the credit note is applied"
        user = self.user
        invoice = self.create_invoice_n_orgas('Invoice0001', discount=0)[0]

        create_line = partial(ProductLine.objects.create, user=user)
        create_line(related_document=invoice, on_the_fly_item='Otf1', unit_price=Decimal("100"))
        create_line(related_document=invoice, on_the_fly_item='Otf2', unit_price=Decimal("200"))

        credit_note = self.create_credit_note_n_orgas('Credit Note 001')[0]
        create_line(related_document=credit_note, on_the_fly_item='Otf3', unit_price=Decimal("301"))

        Relation.objects.create(object_entity=invoice, subject_entity=credit_note,
                                type_id=REL_SUB_CREDIT_NOTE_APPLIED, user=user,
                               )

        invoice = self.refresh(invoice)
        expected_total = Decimal('0')
        self.assertEqual(expected_total, invoice.total_no_vat)
        self.assertEqual(expected_total, invoice.total_vat)

    @skipIfCustomInvoice
    @skipIfCustomProductLine
    def test_createview03(self):
        "Credit note in a negative Invoice -> a bigger negative Invoice"
        user = self.user
        invoice = self.create_invoice_n_orgas('Invoice0001', discount=0)[0]

        create_line = partial(ProductLine.objects.create, user=user)
        create_line(related_document=invoice, on_the_fly_item='Otf1', unit_price=Decimal("-100"))

        credit_note = self.create_credit_note_n_orgas('Credit Note 001')[0]
        create_line(related_document=credit_note, on_the_fly_item='Otf3', unit_price=Decimal("1"))

        Relation.objects.create(object_entity=invoice, subject_entity=credit_note,
                                type_id=REL_SUB_CREDIT_NOTE_APPLIED, user=user,
                               )

        invoice = self.refresh(invoice)
        expected_total = Decimal('-101')
        self.assertEqual(expected_total, invoice.total_no_vat)

    @skipIfCustomInvoice
    @skipIfCustomProductLine
    def test_unlink_from_invoice(self):
        user = self.user
        invoice = self.create_invoice_n_orgas('Invoice0001', discount=0)[0]
        self.assertEqual([], invoice.get_credit_notes())

        create_line = partial(ProductLine.objects.create, user=user)
        create_line(related_document=invoice, on_the_fly_item='Otf1', unit_price=Decimal("100"))
        self.assertEqual(Decimal('100'), self.refresh(invoice).total_no_vat)

        credit_note = self.create_credit_note_n_orgas('Credit Note 001')[0]
        create_line(related_document=credit_note, on_the_fly_item='Otf3', unit_price=Decimal("60"))

        r = Relation.objects.create(object_entity=invoice, subject_entity=credit_note,
                                    type_id=REL_SUB_CREDIT_NOTE_APPLIED, user=user,
                                   )
        self.assertEqual(Decimal('40'), self.refresh(invoice).total_no_vat)
        self.assertEqual([credit_note], self.refresh(invoice).get_credit_notes())

        r.delete()
        self.assertEqual(Decimal('100'), self.refresh(invoice).total_no_vat)
        self.assertEqual([], self.refresh(invoice).get_credit_notes())

    @skipIfCustomInvoice
    @skipIfCustomProductLine
    def test_trash_linked_to_invoice(self):
        user = self.user
        invoice = self.create_invoice_n_orgas('Invoice0001', discount=0)[0]

        create_line = partial(ProductLine.objects.create, user=user)
        create_line(related_document=invoice, on_the_fly_item='Otf1', unit_price=Decimal("100"))
        self.assertEqual(Decimal('100'), self.refresh(invoice).total_no_vat)

        credit_note = self.create_credit_note_n_orgas('Credit Note 001')[0]
        create_line(related_document=credit_note, on_the_fly_item='Otf3', unit_price=Decimal("60"))

        Relation.objects.create(object_entity=invoice, subject_entity=credit_note,
                                type_id=REL_SUB_CREDIT_NOTE_APPLIED, user=user,
                               )
        self.assertEqual(Decimal('40'), self.refresh(invoice).total_no_vat)

        credit_note.trash()
        self.assertTrue(self.refresh(credit_note).is_deleted)
        self.assertEqual([], self.refresh(invoice).get_credit_notes())
        self.assertEqual(Decimal('100'), self.refresh(invoice).total_no_vat)

        credit_note.restore()
        self.assertFalse(self.refresh(credit_note).is_deleted)
        self.assertEqual([credit_note], self.refresh(invoice).get_credit_notes())
        self.assertEqual(Decimal('40'), self.refresh(invoice).total_no_vat)

    def test_delete_status01(self):
        status = CreditNoteStatus.objects.create(name='OK')
        self.assertDeleteStatusOK(status, 'credit_note_status')

    def test_delete_status02(self):
        status = CreditNoteStatus.objects.create(name='OK')
        credit_note = self.create_credit_note_n_orgas('Credit Note 001', status=status)[0]

        self.assertDeleteStatusKO(status, 'credit_note_status', credit_note)

    @skipIfCustomInvoice
    @skipIfCustomProductLine
    def test_addrelated_view(self):
        "Attach credit note to existing invoice"
        user = self.user
        create_line = partial(ProductLine.objects.create, user=user)

        invoice = self.create_invoice_n_orgas('Invoice0001', discount=0)[0]
        invoice_target = invoice.get_target()
        create_line(related_document=invoice, on_the_fly_item='Otf1', unit_price=Decimal("100"))
        create_line(related_document=invoice, on_the_fly_item='Otf2', unit_price=Decimal("200"))

        url = reverse('billing__link_to_cnotes', args=(invoice.id,))
        self.assertGET200(url)

        credit_note_source = Organisation.objects.create(user=user, name='Organisation 003')
        credit_note = self.create_credit_note('Credit Note 001', source=credit_note_source, target=invoice_target)
        create_line(related_document=credit_note, on_the_fly_item='Otf3', unit_price=Decimal("50"))

        self.assertEqual(0, Relation.objects.filter(object_entity=invoice, subject_entity=credit_note).count())
        self.assertInvoiceTotalToPay(invoice, 300)

        response = self.client.post(url, follow=True,
                                    data={'credit_notes': self.formfield_value_multi_creator_entity(credit_note)},
                                   )
        self.assertNoFormError(response)

        self.assertEqual(1, Relation.objects.filter(object_entity=invoice, subject_entity=credit_note).count())
        self.assertInvoiceTotalToPay(invoice, 250)

        # Check invoice view (bug in block_credit_note.html)
        self.assertGET200(invoice.get_absolute_url())

    def test_addrelated_view_no_invoice(self):
        "Cannot attach credit note to invalid invoice"
        self.assertGET404(reverse('billing__link_to_cnotes', args=(12445,)))

    @skipIfCustomInvoice
    @skipIfCustomProductLine
    def test_addrelated_view_not_same_currency(self):
        "Cannot attach credit note in US Dollar to invoice in Euro"
        user = self.user
        create_line = partial(ProductLine.objects.create, user=user)
        us_dollar = Currency.objects.all()[1]

        invoice = self.create_invoice_n_orgas('Invoice0001', discount=0)[0]
        invoice_target = invoice.get_target()
        create_line(related_document=invoice, on_the_fly_item='Otf1', unit_price=Decimal("100"))
        create_line(related_document=invoice, on_the_fly_item='Otf2', unit_price=Decimal("200"))

        url = reverse('billing__link_to_cnotes', args=(invoice.id,))
        self.assertGET200(url)

        credit_note_source = Organisation.objects.create(user=user, name='Organisation 003')
        credit_note = self.create_credit_note('Credit Note 001', source=credit_note_source, target=invoice_target, currency=us_dollar)
        create_line(related_document=credit_note, on_the_fly_item='Otf3', unit_price=Decimal("50"))

        self.assertEqual(0, Relation.objects.filter(object_entity=invoice, subject_entity=credit_note).count())
        self.assertInvoiceTotalToPay(invoice, 300)

        response = self.client.post(url, follow=True, data={'credit_notes': '[{}]'.format(credit_note.id)})
        self.assertFormError(response, 'form', 'credit_notes', _(u'This entity does not exist.'))

        self.assertEqual(0, Relation.objects.filter(object_entity=invoice, subject_entity=credit_note).count())
        self.assertInvoiceTotalToPay(invoice, 300)

        # Check invoice view (bug in block_credit_note.html)
        self.assertGET200(invoice.get_absolute_url())

    @skipIfCustomInvoice
    @skipIfCustomProductLine
    def test_addrelated_view_already_linked(self):
        "cannot attach credit note in US Dollar to invoice in Euro"
        user = self.user
        create_line = partial(ProductLine.objects.create, user=user)
        us_dollar = Currency.objects.all()[1]

        invoice = self.create_invoice_n_orgas('Invoice0001', discount=0)[0]
        invoice_target = invoice.get_target()
        create_line(related_document=invoice, on_the_fly_item='Otf1', unit_price=Decimal("100"))
        create_line(related_document=invoice, on_the_fly_item='Otf2', unit_price=Decimal("200"))

        url = reverse('billing__link_to_cnotes', args=(invoice.id,))
        self.assertGET200(url)

        credit_note_source = Organisation.objects.create(user=user, name='Organisation 003')
        credit_note = self.create_credit_note('Credit Note 001', source=credit_note_source,
                                              target=invoice_target, currency=us_dollar,
                                             )
        create_line(related_document=credit_note, on_the_fly_item='Otf3', unit_price=Decimal("50"))

        Relation.objects.create(object_entity=invoice, subject_entity=credit_note,
                                type_id=REL_SUB_CREDIT_NOTE_APPLIED, user=user,
                               )

        self.assertEqual(1, Relation.objects.filter(object_entity=invoice, subject_entity=credit_note).count())
        self.assertInvoiceTotalToPay(invoice, 250)

        response = self.client.post(url, follow=True,
                                    data={'credit_notes': self.formfield_value_multi_creator_entity(credit_note)},
                                   )
        self.assertFormError(response, 'form', 'credit_notes', _(u'This entity does not exist.'))

        self.assertEqual(1, Relation.objects.filter(object_entity=invoice, subject_entity=credit_note).count())
        self.assertInvoiceTotalToPay(invoice, 250)

        # Check invoice view (bug in block_credit_note.html)
        self.assertGET200(invoice.get_absolute_url())

    @skipIfCustomInvoice
    @skipIfCustomProductLine
    def test_addrelated_view_already_not_same_target(self):
        "Cannot attach credit note in US Dollar to invoice in Euro"
        user = self.user
        create_line = partial(ProductLine.objects.create, user=user)

        invoice = self.create_invoice_n_orgas('Invoice0001', discount=0)[0]
        create_line(related_document=invoice, on_the_fly_item='Otf1', unit_price=Decimal("100"))
        create_line(related_document=invoice, on_the_fly_item='Otf2', unit_price=Decimal("200"))

        url = reverse('billing__link_to_cnotes', args=(invoice.id,))
        self.assertGET200(url)

        credit_note_source = Organisation.objects.create(user=user, name='Organisation 003')
        credit_note_target = Organisation.objects.create(user=user, name='Organisation 004')
        credit_note = self.create_credit_note('Credit Note 001', source=credit_note_source, target=credit_note_target)
        create_line(related_document=credit_note, on_the_fly_item='Otf3', unit_price=Decimal("50"))

        self.assertEqual(0, Relation.objects.filter(object_entity=invoice, subject_entity=credit_note).count())
        self.assertInvoiceTotalToPay(invoice, 300)

        response = self.client.post(url, follow=True, data={'credit_notes': '[{}]'.format(credit_note.id)})
        self.assertFormError(response, 'form', 'credit_notes', _(u'This entity does not exist.'))

        self.assertEqual(0, Relation.objects.filter(object_entity=invoice, subject_entity=credit_note).count())
        self.assertInvoiceTotalToPay(invoice, 300)

    @skipIfCustomInvoice
    @skipIfCustomProductLine
    def test_deleterelated_view(self):
        user = self.user
        create_line = partial(ProductLine.objects.create, user=user)

        invoice = self.create_invoice_n_orgas('Invoice0001', discount=0)[0]
        invoice_target = invoice.get_target()
        create_line(related_document=invoice, on_the_fly_item='Otf1', unit_price=Decimal("100"))

        credit_note_source = Organisation.objects.create(user=user, name='Organisation 003')
        credit_note = self.create_credit_note('Credit Note 001', source=credit_note_source, target=invoice_target)
        create_line(related_document=credit_note, on_the_fly_item='Otf3', unit_price=Decimal("50"))

        Relation.objects.create(object_entity=invoice, subject_entity=credit_note,
                                type_id=REL_SUB_CREDIT_NOTE_APPLIED, user=user,
                               )

        self.assertEqual(1, Relation.objects.filter(object_entity=invoice, subject_entity=credit_note).count())
        self.assertInvoiceTotalToPay(invoice, 50)

        response = self.client.post(self._build_deleterelated_url(credit_note, invoice), follow=True)

        self.assertNoFormError(response)

        self.assertEqual(0, Relation.objects.filter(object_entity=invoice, subject_entity=credit_note).count())
        self.assertInvoiceTotalToPay(invoice, 100)

    @skipIfCustomInvoice
    @skipIfCustomProductLine
    def test_deleterelated_view_not_exists(self):
        user = self.user
        create_line = partial(ProductLine.objects.create, user=user)

        invoice = self.create_invoice_n_orgas('Invoice0001', discount=0)[0]
        invoice_target = invoice.get_target()
        create_line(related_document=invoice, on_the_fly_item='Otf1', unit_price=Decimal("100"))

        credit_note_source = Organisation.objects.create(user=user, name='Organisation 003')
        credit_note = self.create_credit_note('Credit Note 001', source=credit_note_source, target=invoice_target)
        create_line(related_document=credit_note, on_the_fly_item='Otf3', unit_price=Decimal("50"))

        self.assertEqual(0, Relation.objects.filter(object_entity=invoice, subject_entity=credit_note).count())
        self.assertInvoiceTotalToPay(invoice, 100)

        self.assertPOST404(self._build_deleterelated_url(credit_note, invoice), follow=True)

        self.assertEqual(0, Relation.objects.filter(object_entity=invoice, subject_entity=credit_note).count())
        self.assertInvoiceTotalToPay(invoice, 100)

    @skipIfCustomInvoice
    @skipIfCustomProductLine
    def test_deleterelated_view_not_allowed(self):
        user = self.user
        create_line = partial(ProductLine.objects.create, user=user)

        invoice = self.create_invoice_n_orgas('Invoice0001', discount=0)[0]
        invoice_target = invoice.get_target()
        create_line(related_document=invoice, on_the_fly_item='Otf1', unit_price=Decimal("100"))

        credit_note_source = Organisation.objects.create(user=user, name='Organisation 003')
        credit_note = self.create_credit_note('Credit Note 001', source=credit_note_source, target=invoice_target)
        create_line(related_document=credit_note, on_the_fly_item='Otf3', unit_price=Decimal("50"))

        Relation.objects.create(object_entity=invoice, subject_entity=credit_note,
                                type_id=REL_SUB_CREDIT_NOTE_APPLIED, user=user,
                               )

        self.assertEqual(1, Relation.objects.filter(object_entity=invoice, subject_entity=credit_note).count())
        self.assertInvoiceTotalToPay(invoice, 50)

        self.client.logout()
        self.client.login(username=self.other_user.username, password='test')

        self.assertPOST403(self._build_deleterelated_url(credit_note, invoice), follow=True)

        self.assertEqual(1, Relation.objects.filter(object_entity=invoice, subject_entity=credit_note).count())
        self.assertInvoiceTotalToPay(invoice, 50)

    def test_editcomment01(self):
        FieldsConfig.create(CreditNote,
                            descriptions=[('issuing_date', {FieldsConfig.HIDDEN: True})],
                           )

        credit_note = self.create_credit_note_n_orgas('Credit Note 001')[0]

        url = self._build_editcomment_url(credit_note)
        self.assertGET200(url)

        comment = 'Special gift'
        self.assertNoFormError(self.client.post(url, data={'comment': comment}))
        self.assertEqual(comment, self.refresh(credit_note).comment)

    def test_editcomment02(self):
        "'comment' is hidden"
        FieldsConfig.create(CreditNote,
                            descriptions=[('comment', {FieldsConfig.HIDDEN: True})],
                           )

        credit_note = self.create_credit_note_n_orgas('Credit Note 001')[0]
        self.assertGET409(self._build_editcomment_url(credit_note))

    # TODO: complete (other views)
