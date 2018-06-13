# -*- coding: utf-8 -*-

try:
    from json import dumps as json_dump

    from django.urls import reverse

    from creme.creme_core.tests.forms.base import FieldTestCase

    from .base import Document, _DocumentsTestCase
    from ..forms.fields import ImageEntityField, MultiImageEntityField
except Exception as e:
    print('Error in <{}>: {}'.format(__name__, e))


class ImageEntityFieldTestCase(_DocumentsTestCase, FieldTestCase):
    def setUp(self):
        super(ImageEntityFieldTestCase, self).setUp()
        self.login()

    def test_init01(self):
        "Not required"
        with self.assertNumQueries(0):
            field = ImageEntityField(required=False)

        self.assertFalse(field.required)
        self.assertEqual(Document, field.model)
        self.assertEqual(Document, field.widget.model)
        self.assertTrue(field.force_creation)
        self.assertEqual({'mime_type__name__startswith': 'image/'}, field.q_filter)

        url = reverse('documents__create_image_popup')
        self.assertEqual(url, field.create_action_url)
        self.assertFalse(field.widget.creation_url)
        self.assertFalse(field.widget.creation_allowed)

        field.user = self.user
        self.assertEqual(url, field.widget.creation_url)
        self.assertTrue(field.widget.creation_allowed)

    def test_clean01(self):
        "Not required"
        field = ImageEntityField(required=False)
        field.user = self.user
        self.assertIsNone(field.clean(''))

        img = self._create_image()
        self.assertEqual(img, field.clean(str(img.id)))

        doc = self._create_doc('foobar.txt')
        self.assertIsNone(field.clean(str(doc.id)))

    def test_clean02(self):
        "Required"
        field = ImageEntityField(user=self.user)

        self.assertTrue(field.required)
        self.assertFieldValidationError(ImageEntityField, 'required', field.clean, '')

        doc = self._create_doc('foobar.txt')
        self.assertFieldValidationError(ImageEntityField, 'doesnotexist', field.clean, str(doc.id))

    def test_qfilter_init(self):
        field = ImageEntityField(user=self.user, q_filter={'title__icontains': 'show'})

        final_qfilter = {
            'mime_type__name__startswith': 'image/',
            'title__icontains':            'show',
        }
        self.assertEqual(final_qfilter, field.q_filter)
        self.assertFalse(field.force_creation)

        # Widget
        self.assertEqual(final_qfilter, field.widget.q_filter)
        self.assertFalse(field.widget.creation_url)
        self.assertTrue(field.widget.creation_allowed)

        # Clean
        img1 = self._create_image(title='Icon#1', ident=1)
        self.assertFieldValidationError(ImageEntityField, 'doesnotexist', field.clean, str(img1.id))

        img2 = self._create_image(title='Python Show 2018', ident=2)
        self.assertEqual(img2, field.clean(str(img2.id)))

    def test_qfilter_property(self):
        field = ImageEntityField(user=self.user)
        field.q_filter = {'title__contains': 'show'}

        final_qfilter = {
            'mime_type__name__startswith': 'image/',
            'title__contains':             'show',
        }
        self.assertEqual(final_qfilter, field.q_filter)
        self.assertFalse(field.force_creation)

        # Widget
        self.assertEqual(final_qfilter, field.widget.q_filter)
        self.assertFalse(field.widget.creation_url)
        self.assertTrue(field.widget.creation_allowed)

        # Clean
        img1 = self._create_image(title='Icon#1')
        self.assertFieldValidationError(ImageEntityField, 'doesnotexist', field.clean, str(img1.id))

        img2 = self._create_image(title='Python show 2018')
        self.assertEqual(img2, field.clean(str(img2.id)))

    def test_force_creation(self):
        field = ImageEntityField(user=self.user)
        self.assertTrue(field.force_creation)

        url = reverse('documents__create_image_popup')
        self.assertEqual(url, field.widget.creation_url)
        self.assertTrue(field.widget.creation_allowed)

        field.force_creation = False
        self.assertFalse(field.widget.creation_url)

        field.force_creation = True
        self.assertEqual(url, field.widget.creation_url)

    def test_creation_url_init(self):
        creation_url = '/documents/create_image_v2/'

        field = ImageEntityField(create_action_url=creation_url)
        self.assertEqual(creation_url, field.create_action_url)
        self.assertFalse(field.widget.creation_url)
        self.assertTrue(field.force_creation)

        field.user = self.user
        self.assertEqual(creation_url, field.widget.creation_url)

    def test_creation_url_property(self):
        creation_url = '/documents/create_image_v2/'

        field = ImageEntityField()
        field.create_action_url = creation_url
        self.assertEqual(creation_url, field.create_action_url)
        self.assertFalse(field.widget.creation_url)
        self.assertTrue(field.force_creation)

        field.user = self.user
        self.assertEqual(creation_url, field.widget.creation_url)
        self.assertTrue(field.widget.creation_allowed)


class MultiImageEntityFieldTestCase(_DocumentsTestCase, FieldTestCase):
    def setUp(self):
        super(MultiImageEntityFieldTestCase, self).setUp()
        self.login()

    @staticmethod
    def _build_value(*docs):
        return json_dump([doc.id for doc in docs])

    def test_init01(self):
        "Not required"
        with self.assertNumQueries(0):
            field = MultiImageEntityField(required=False)

        self.assertFalse(field.required)
        self.assertEqual(Document, field.model)
        self.assertEqual(Document, field.widget.model)
        self.assertTrue(field.force_creation)
        self.assertEqual({'mime_type__name__startswith': 'image/'}, field.q_filter)

        url = reverse('documents__create_image_popup')
        self.assertEqual(url, field.create_action_url)
        self.assertFalse(field.widget.creation_url)
        self.assertFalse(field.widget.creation_allowed)

        field.user = self.user
        self.assertEqual(url, field.widget.creation_url)
        self.assertTrue(field.widget.creation_allowed)

    def test_clean01(self):
        "Not required"
        field = MultiImageEntityField(required=False)
        field.user = self.user
        self.assertEqual([], field.clean('[]'))

        img = self._create_image()
        self.assertEqual([img], field.clean(self._build_value(img)))

        doc = self._create_doc('foobar.txt')
        # self.assertEqual([], field.clean(json_dump([doc.id]))) TODO ?
        self.assertFieldValidationError(MultiImageEntityField, 'doesnotexist', field.clean, self._build_value(doc))

    def test_clean02(self):
        "Required"
        field = MultiImageEntityField(user=self.user)

        self.assertTrue(field.required)
        self.assertFieldValidationError(ImageEntityField, 'required', field.clean, '[]')

        doc = self._create_doc('foobar.txt')
        self.assertFieldValidationError(ImageEntityField, 'doesnotexist', field.clean, self._build_value(doc))

    def test_qfilter_init(self):
        field = MultiImageEntityField(user=self.user, q_filter={'title__contains': 'show'})

        final_qfilter = {
            'mime_type__name__startswith': 'image/',
            'title__contains':             'show',
        }
        self.assertEqual(final_qfilter, field.q_filter)
        self.assertFalse(field.force_creation)

        # Widget
        self.assertEqual(final_qfilter, field.widget.q_filter)
        self.assertFalse(field.widget.creation_url)
        self.assertTrue(field.widget.creation_allowed)

        # Clean
        img1 = self._create_image(title='Icon#1')
        self.assertFieldValidationError(ImageEntityField, 'doesnotexist', field.clean, self._build_value(img1))

        img2 = self._create_image(title='Python show 2018')
        img3 = self._create_image(title='Python show 2019')
        self.assertEqual([img2, img3], field.clean(self._build_value(img2, img3)))

    def test_qfilter_property(self):
        field = MultiImageEntityField(user=self.user)
        field.q_filter = {'title__icontains': 'show'}

        final_qfilter = {
            'mime_type__name__startswith': 'image/',
            'title__icontains':            'show',
        }
        self.assertEqual(final_qfilter, field.q_filter)
        self.assertFalse(field.force_creation)

        # Widget
        self.assertEqual(final_qfilter, field.widget.q_filter)
        self.assertFalse(field.widget.creation_url)
        self.assertTrue(field.widget.creation_allowed)

        # Clean
        img1 = self._create_image(title='Icon#1')
        self.assertFieldValidationError(ImageEntityField, 'doesnotexist', field.clean, self._build_value(img1))

        img2 = self._create_image(title='Python Show 2018')
        self.assertEqual([img2], field.clean(self._build_value(img2)))

    def test_force_creation(self):
        field = MultiImageEntityField(user=self.user)
        self.assertTrue(field.force_creation)

        url = reverse('documents__create_image_popup')
        self.assertEqual(url, field.widget.creation_url)
        self.assertTrue(field.widget.creation_allowed)

        field.force_creation = False
        self.assertFalse(field.widget.creation_url)

        field.force_creation = True
        self.assertEqual(url, field.widget.creation_url)

    def test_creation_url_init(self):
        creation_url = '/documents/create_image_v2/'

        field = MultiImageEntityField(create_action_url=creation_url)
        self.assertEqual(creation_url, field.create_action_url)
        self.assertFalse(field.widget.creation_url)
        self.assertTrue(field.force_creation)

        field.user = self.user
        self.assertEqual(creation_url, field.widget.creation_url)

    def test_creation_url_property(self):
        creation_url = '/documents/create_image_v2/'

        field = MultiImageEntityField()
        field.create_action_url = creation_url
        self.assertEqual(creation_url, field.create_action_url)
        self.assertFalse(field.widget.creation_url)
        self.assertTrue(field.force_creation)

        field.user = self.user
        self.assertEqual(creation_url, field.widget.creation_url)
        self.assertTrue(field.widget.creation_allowed)
