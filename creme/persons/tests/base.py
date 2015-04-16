# -*- coding: utf-8 -*-

from creme.creme_core.tests.base import CremeTestCase


class _BaseTestCase(CremeTestCase):
    def login(self, is_superuser=True, **kwargs):
        return super(_BaseTestCase, self).login(is_superuser, allowed_apps=['persons'], **kwargs)

    @classmethod
    def setUpClass(cls):
        CremeTestCase.setUpClass()
        cls.populate('creme_core', 'persons')
        cls.autodiscover()

    def assertAddressOnlyContentEqual(self, address1, address2):
        self.assertNotEqual(address1.id, address2.id)

        for attr in ['city', 'state', 'zipcode', 'country', 'department', 'content_type']:
            self.assertEqual(getattr(address1, attr), getattr(address2, attr))
