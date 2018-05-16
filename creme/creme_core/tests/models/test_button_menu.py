# -*- coding: utf-8 -*-

try:
    from ..base import CremeTestCase
    from ..fake_models import FakeContact
    from creme.creme_core.models import ButtonMenuItem
    from creme.creme_core.gui.button_menu import Button
except Exception as e:
    print('Error in <%s>: %s' % (__name__, e))


class ButtonMenuItemTestCase(CremeTestCase):
    def test_create_if_needed01_legacy(self):
        "Use instance"
        pk = 'creme_core-test_button'
        self.assertFalse(ButtonMenuItem.objects.filter(pk=pk))

        class TestButton(Button):
            id_          = Button.generate_id('creme_core', 'test_create_if_needed01')
            verbose_name = u'Testing purpose'

        button = TestButton()

        order = 10
        ButtonMenuItem.create_if_needed(pk, FakeContact, button, order)
        bmi = self.get_object_or_fail(ButtonMenuItem, pk=pk)

        self.assertEqual(FakeContact, bmi.content_type.model_class())
        self.assertEqual(button.id_, bmi.button_id)
        self.assertEqual(order,      bmi.order)

        old_count = ButtonMenuItem.objects.count()
        bmi = ButtonMenuItem.create_if_needed(pk, FakeContact, button, order + 5)
        self.assertEqual(order,     bmi.order)
        self.assertEqual(old_count, ButtonMenuItem.objects.count())

    def test_create_if_needed01(self):
        pk = 'creme_core-test_button'
        self.assertFalse(ButtonMenuItem.objects.filter(pk=pk))

        class TestButton(Button):
            id_          = Button.generate_id('creme_core', 'test_create_if_needed01')
            verbose_name = u'Testing purpose'

        order = 10
        ButtonMenuItem.create_if_needed(pk, FakeContact, TestButton, order)
        bmi = self.get_object_or_fail(ButtonMenuItem, pk=pk)

        self.assertEqual(FakeContact,    bmi.content_type.model_class())
        self.assertEqual(TestButton.id_, bmi.button_id)
        self.assertEqual(order,          bmi.order)

        old_count = ButtonMenuItem.objects.count()
        bmi = ButtonMenuItem.create_if_needed(pk, FakeContact, TestButton, order + 5)
        self.assertEqual(order,     bmi.order)
        self.assertEqual(old_count, ButtonMenuItem.objects.count())

    def test_create_if_needed02(self):
        "Default config (content_type=None)"
        class TestButton(Button):
            id_          = Button.generate_id('creme_core', 'test_create_if_needed02')
            verbose_name = u'Testing purpose'

        # button = TestButton()

        old_count = ButtonMenuItem.objects.count()
        # bmi = ButtonMenuItem.create_if_needed('creme_core-test_button', None, button, 15)
        bmi = ButtonMenuItem.create_if_needed('creme_core-test_button', None, TestButton, 15)
        self.assertEqual(old_count + 1, ButtonMenuItem.objects.count())
        self.assertIsNone(bmi.content_type)

    def test_create_if_needed03(self):  # TODO: remove this test when pkstring is removed
        "PK collision"
        class TestButton(Button):
            id_          = Button.generate_id('creme_core', 'test_create_if_needed03')
            verbose_name = u'Testing purpose'

        # button = TestButton()

        old_count = ButtonMenuItem.objects.count()
        # ButtonMenuItem.create_if_needed('creme_core-test_button', None, button, 15)
        ButtonMenuItem.create_if_needed('creme_core-test_button', None, TestButton, 15)
        self.assertEqual(old_count + 1, ButtonMenuItem.objects.count())

        TestButton.id_ = Button.generate_id('creme_core', 'test_create_if_needed03_bis')

        with self.assertNoException():
            # ButtonMenuItem.create_if_needed('creme_core-test_button', None, button, 15)
            ButtonMenuItem.create_if_needed('creme_core-test_button', None, TestButton, 15)

        self.assertEqual(old_count + 1, ButtonMenuItem.objects.count())
