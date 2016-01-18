# -*- coding: utf-8 -*-

try:
    from functools import partial

    from creme.creme_core.tests.forms.base import FieldTestCase

    from ..models import Category, SubCategory
    from ..forms.fields import CategoryField
except Exception as e:
    print('Error in <%s>: %s' % (__name__, e))


class CategoryFieldTestCase(FieldTestCase):
    format_str = '{"category": %s, "subcategory": %s}'

    @classmethod
    def setUpClass(cls):
        FieldTestCase.setUpClass()
        SubCategory.objects.all().delete()
        Category.objects.all().delete()

    def test_void(self):
        cat1 = Category.objects.create(name='cat1', description='description')
        cat11 = SubCategory.objects.create(name='sub11', description='description', category=cat1)

        with self.assertNumQueries(0):
            field = CategoryField()

        self.assertEqual(cat11, field.clean(self.format_str % (cat1.id, cat11.id)))

    def test_categories01(self):
        create_cat = partial(Category.objects.create, description='description')
        cat1 = create_cat(name='cat1')
        cat2 = create_cat(name='cat2')

        field = CategoryField()
        self.assertEqual([cat1, cat2], list(field.categories))

    def test_categories02(self):
        "Fixed Categories"
        create_cat = partial(Category.objects.create, description='description')
        cat1 = create_cat(name='cat1')
        cat2 = create_cat(name='cat2')
        create_cat(name='cat3')

        field = CategoryField(categories=[cat1.id, cat2.id])

        self.assertEqual([cat1, cat2], list(field.categories))

    def test_format_object(self):
        cat1 = Category.objects.create(name='cat1', description='description')

        create_subcat = partial(SubCategory.objects.create, category=cat1)
        cat11 = create_subcat(name='sub11', description='description')
        cat12 = create_subcat(name='sub12', description='description')

        from_python = CategoryField(categories=[cat1.id]).from_python
        format_str = self.format_str
        self.assertEqual(format_str % (cat1.id, cat11.id), from_python((cat1.id, cat11.id)))
        self.assertEqual(format_str % (cat1.id, cat11.id), from_python(cat11))
        self.assertEqual(format_str % (cat1.id, cat12.id), from_python(cat12))

    def test_clean_empty_required(self):
        clean = CategoryField(required=True).clean
        self.assertFieldValidationError(CategoryField, 'required', clean, None)
        self.assertFieldValidationError(CategoryField, 'required', clean, '{}')

    def test_clean_empty_not_required(self):
        clean = CategoryField(required=False).clean

        with self.assertNoException():
            value = clean(None)

        self.assertIsNone(value)

        with self.assertNoException():
            value = clean('{}')

        self.assertIsNone(value)

    def test_clean_invalid_json(self):
        clean = CategoryField(required=False).clean
        self.assertFieldValidationError(CategoryField, 'invalidformat', clean,
                                        '{"category":"12","subcategory":"1"'
                                       )

    def test_clean_invalid_data_type(self):
        clean = CategoryField(required=False).clean
        self.assertFieldValidationError(CategoryField, 'invalidtype', clean, '"this is a string"')
        self.assertFieldValidationError(CategoryField, 'invalidtype', clean, "12")

    def test_clean_invalid_data(self):
        clean = CategoryField(required=False).clean
        self.assertFieldValidationError(CategoryField, 'invalidformat', clean, '{"category":"notanumber","subcategory":"1"}')
        self.assertFieldValidationError(CategoryField, 'invalidformat', clean, '{"category":"12","category":"notanumber"}')

    def test_clean_incomplete_data_required(self):
        clean = CategoryField().clean
        self.assertFieldValidationError(CategoryField, 'required', clean, '{"category":"1"}')
        self.assertFieldValidationError(CategoryField, 'required', clean, '{"category":"12"}')

    def test_clean_unallowed_category(self):
        "Data injection : forbidden category"
        cat1 = Category.objects.create(name='cat1', description='description')

        cat2 = Category.objects.create(name='cat2', description='description')
        cat21 = SubCategory.objects.create(name='sub21', description='description', category=cat2)

        with self.assertNumQueries(0):
            field = CategoryField(categories=[cat1.id])

        value = self.format_str % (cat2.id, cat21.id)
        self.assertFieldValidationError(CategoryField, 'categorynotallowed', field.clean, value)

    def test_clean_unknown_category(self):
        "Data injection : category doesn't exist"
        cat1 = Category.objects.create(name='cat1', description='description')
        cat11 = SubCategory.objects.create(name='sub11', description='description', category=cat1)

        clean = CategoryField(categories=[cat1.id, 0]).clean
        # Same error than 'forbidden', cause unknown category cannot be in list
        self.assertFieldValidationError(CategoryField, 'categorynotallowed', clean,
                                        self.format_str % (0, cat11.id)
                                       )

    def test_clean_unknown_subcategory(self):
        "Data injection : subcategory doesn't exist"
        cat1 = Category.objects.create(name='cat1', description='description')

        field = CategoryField(categories=[cat1.id])
        value = self.format_str % (cat1.id, 0)
        self.assertTrue(field.required)
        self.assertFieldValidationError(CategoryField, 'doesnotexist', field.clean, value)

        field.required = False
        self.assertFieldValidationError(CategoryField, 'doesnotexist', field.clean, value)

    def test_clean_invalid_category_pair(self):
        "Data injection : use incompatible category/subcategory pair"
        cat1 = Category.objects.create(name='cat1', description='description')

        cat2 = Category.objects.create(name='cat2', description='description')
        cat21 = SubCategory.objects.create(name='sub21', description='description', category=cat2)

        clean = CategoryField(categories=[cat1.id, cat2.id]).clean
        self.assertFieldValidationError(CategoryField, 'subcategorynotallowed', clean,
                                        self.format_str % (cat1.id, cat21.id)
                                       )

    def test_clean01(self):
        cat1 = Category.objects.create(name='cat1', description='description')
        cat11 = SubCategory.objects.create(name='sub11', description='description', category=cat1)

        field = CategoryField(categories=[cat1.id])
        self.assertEqual(cat11, field.clean(self.format_str % (cat1.id, cat11.id)))

    def test_clean02(self):
        "Use 'categories' setter"
        cat1 = Category.objects.create(name='cat1', description='description')
        cat11 = SubCategory.objects.create(name='sub11', description='description', category=cat1)

        field = CategoryField()
        field.categories = [cat1.id]
        self.assertEqual(cat11, field.clean(self.format_str % (cat1.id, cat11.id)))
