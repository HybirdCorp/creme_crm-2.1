# -*- coding: utf-8 -*-

from django.test import TestCase
from django.db.models import fields
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType

from creme_core import models
from creme_core.utils import meta, chunktools


class MetaTestCase(TestCase):
    def test_get_field_infos(self):
        text = 'TEXT'

        user   = User.objects.create(username='name')
        ptype  = models.CremePropertyType.objects.create(text=text, is_custom=True)
        entity = models.CremeEntity.objects.create(user=user)
        prop   = models.CremeProperty(type=ptype, creme_entity=entity)

        self.assertEqual((fields.CharField,    text), meta.get_field_infos(prop, 'type__text'))
        self.assertEqual((fields.BooleanField, True), meta.get_field_infos(prop, 'type__is_custom'))

        self.assertEqual((None, ''), meta.get_field_infos(prop, 'foobar__is_custom'))
        self.assertEqual((None, ''), meta.get_field_infos(prop, 'type__foobar'))

        self.assertEqual(fields.CharField, meta.get_field_infos(prop, 'creme_entity__entity_type__name')[0])

    def test_get_model_field_infos(self):
        self.assertEqual([], meta.get_model_field_infos(models.CremeEntity, 'foobar'))
        self.assertEqual([], meta.get_model_field_infos(models.CremeEntity, 'foo__bar'))

        #[{'field': <django.db.models.fields.related.ForeignKey object at ...>,
        #  'model': <class 'creme_core.models.creme_property.CremePropertyType'>}]
        try:
            info = meta.get_model_field_infos(models.CremeProperty, 'type')
            self.assertEqual(1, len(info))

            desc = info[0]
            self.assert_(isinstance(desc['field'], fields.related.ForeignKey))
            self.assertEqual(models.CremePropertyType, desc['model'])
        except Exception, e:
            self.fail(str(e))

        #[{ 'field': <django.db.models.fields.related.ForeignKey object at ...>,
        #   'model': <class 'creme_core.models.creme_property.CremePropertyType'>},
        # {'field': <django.db.models.fields.CharField object at ...>,
        #   'model': None}]
        try:
            info = meta.get_model_field_infos(models.CremeProperty, 'type__text')
            self.assertEqual(2, len(info))

            desc = info[0]
            self.assert_(isinstance(desc['field'], fields.related.ForeignKey))
            self.assertEqual(models.CremePropertyType, desc['model'])

            desc = info[1]
            self.assert_(isinstance(desc['field'], fields.CharField))
            self.assert_(desc['model'] is None)
        except Exception, e:
            self.fail(str(e))

        #[{'field': <django.db.models.fields.related.ForeignKey object at 0x9d123ec>,
        #  'model': <class 'creme_core.models.entity.CremeEntity'>},
        # {'field': <django.db.models.fields.related.ForeignKey object at 0x9d0378c>,
        #  'model': <class 'django.contrib.contenttypes.models.ContentType'>},
        # {'field': <django.db.models.fields.CharField object at 0x99d302c>,
        #  'model': None}]
        try:
            info = meta.get_model_field_infos(models.CremeProperty, 'creme_entity__entity_type__name')
            self.assertEqual(3, len(info))

            desc = info[0]
            self.assert_(isinstance(desc['field'], fields.related.ForeignKey))
            self.assertEqual(models.CremeEntity, desc['model'])

            desc = info[1]
            self.assert_(isinstance(desc['field'], fields.related.ForeignKey))
            self.assertEqual(ContentType, desc['model'])

            desc = info[2]
            self.assert_(isinstance(desc['field'], fields.CharField))
            self.assert_(desc['model'] is None)
        except Exception, e:
            self.fail(str(e))

    def test_get_date_fields(self):
        entity = models.CremeEntity()
        get_field = entity._meta.get_field
        self.assert_(meta.is_date_field(get_field('created')))
        self.failIf(meta.is_date_field(get_field('user')))

        datefields = meta.get_date_fields(entity)
        self.assertEqual(2, len(datefields))
        self.assertEqual(set(('created', 'modified')), set(f.name for f in datefields))

    #TODO: test get_flds_with_fk_flds etc...


class ChunkToolsTestCase(TestCase):
    data = """04 05 99 66 54
055 6 5322 1 2

98

    456456 455 12
        45 156
dfdsfds
s556"""

    def assert_entries(self, entries):
        self.assertEqual(6, len(entries))
        self.assertEqual('0405996654',  entries[0])
        self.assertEqual('0556532212',  entries[1])
        self.assertEqual('98',          entries[2])
        self.assertEqual('45645645512', entries[3])
        self.assertEqual('45156',       entries[4])
        self.assertEqual('556',         entries[5])

    def chunks(self, chunk_size):
        for chunk in chunktools.iter_as_chunk(self.data, chunk_size):
            yield ''.join(chunk)

    @staticmethod
    def filter(entry):
        return ''.join(char for char in entry if char.isdigit())

    def test_iter_as_slices01(self):
        chunks = list(chunktools.iter_as_slices(self.data, 1000))

        self.assertEqual(1, len(chunks))
        self.assertEqual(self.data, ''.join(chunks))

    def test_iter_as_slices02(self):
        assert len(self.data) % 5 == 0
        chunks = list(chunktools.iter_as_slices(self.data, 5))

        self.assertEqual(16, len(chunks))

        for i, chunk in enumerate(chunks):
            self.assertEqual(5, len(chunk), 'Bad size for chunk %i : %s' % (i, chunk))

        self.assertEqual(self.data, ''.join(chunks))

    def test_iter_as_slices03(self):
        data = self.data + '9'
        assert len(data) % 5 == 1
        chunks = list(chunktools.iter_as_slices(data, 5))

        self.assertEqual(17, len(chunks))

        for i, chunk in enumerate(chunks[:-1]):
            self.assertEqual(5, len(chunk), 'Bad size for chunk %i : %s' % (i, chunk))

        self.assertEqual('9', chunks[-1])

        self.assertEqual(data, ''.join(chunks))

    def test_iter_as_chunks01(self):
        chunks = list(chunktools.iter_as_chunk(self.data, 1000))
        self.assertEqual(1, len(chunks))
        self.assertEqual(self.data, ''.join(chunks[0]))

    def test_iter_as_chunks02(self):
        assert len(self.data) % 5 == 0
        chunks = list(chunktools.iter_as_chunk(self.data, 5))

        self.assertEqual(16, len(chunks))

        for i, chunk in enumerate(chunks):
            self.assertEqual(5, len(chunk), 'Bad size for chunk %i : %s' % (i, chunk))
            self.assert_(isinstance(chunk, list))

        self.assertEqual(self.data, ''.join(''.join(chunk) for chunk in chunks))

    def test_iter_as_chunks03(self):
        data = self.data + '9'
        assert len(data) % 5 == 1
        chunks = list(chunktools.iter_as_chunk(data, 5))

        self.assertEqual(17, len(chunks))

        for i, chunk in enumerate(chunks[:-1]):
            self.assertEqual(5, len(chunk), 'Bad size for chunk %i : %s' % (i, chunk))

        self.assertEqual(['9'], chunks[-1])

        self.assertEqual(data, ''.join(''.join(chunk) for chunk in chunks))

    def test_iter_splitchunks01(self):
        #Tests small_chunks
        chunk_size = 5
        entries = list(chunktools.iter_splitchunks(self.chunks(chunk_size), '\n', ChunkToolsTestCase.filter))

        self.assert_entries(entries)

    def test_iter_splitchunks02(self):
        #Test big_chunks
        chunk_size = len(self.data) / 2
        entries = list(chunktools.iter_splitchunks(self.chunks(chunk_size), '\n', ChunkToolsTestCase.filter))

        self.assert_entries(entries)

    def test_iter_splitchunks03(self):
        #Test with one chunk
        chunk_size = len(self.data) * 2
        entries = list(chunktools.iter_splitchunks(self.chunks(chunk_size), '\n', ChunkToolsTestCase.filter))

        self.assert_entries(entries)
