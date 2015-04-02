# -*- coding: utf-8 -*-

from creme.creme_core.tests.base import CremeTestCase


class _ProductsTestCase(CremeTestCase):
    @classmethod
    def setUpClass(cls):
        CremeTestCase.setUpClass()
        #cls.populate('creme_core', 'creme_config', 'products')
        cls.populate('products')

    def _cat_field(self, category, sub_category):
        return '{"category": %s, "subcategory": %s}' % (category.id, sub_category.id)
