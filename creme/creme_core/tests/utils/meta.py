# -*- coding: utf-8 -*-

try:
    from django.contrib.auth import get_user_model
    from django.contrib.contenttypes.models import ContentType
    from django.db.models import fields, FieldDoesNotExist
    from django.utils.translation import ugettext as _

    from ..base import CremeTestCase #, skipIfNotInstalled
    from ..fake_models import (FakeContact as Contact,
            FakeOrganisation as Organisation, FakeImage as Image,
            FakeEmailCampaign as EmailCampaign, FakeActivity)
    from creme.creme_core.models import CremePropertyType, CremeProperty, CremeEntity
    from creme.creme_core.utils import meta

#    from creme.media_managers.models import Image

#    from creme.persons.models import Contact, Organisation
except Exception as e:
    print('Error in <%s>: %s' % (__name__, e))


__all__ = ('MetaTestCase',)


class MetaTestCase(CremeTestCase):
    def test_get_instance_field_info(self):
        text = 'TEXT'

        user   = get_user_model().objects.create(username='name')
        ptype  = CremePropertyType.objects.create(text=text, is_custom=True)
        entity = CremeEntity.objects.create(user=user)
        prop   = CremeProperty(type=ptype, creme_entity=entity)

        self.assertEqual((fields.CharField,    text), meta.get_instance_field_info(prop, 'type__text'))
        self.assertEqual((fields.BooleanField, True), meta.get_instance_field_info(prop, 'type__is_custom'))

        self.assertEqual((None, ''), meta.get_instance_field_info(prop, 'foobar__is_custom'))
        self.assertEqual((None, ''), meta.get_instance_field_info(prop, 'type__foobar'))

        self.assertEqual(fields.CharField, meta.get_instance_field_info(prop, 'creme_entity__entity_type__name')[0])

    def test_get_model_field_info01(self):
        self.assertEqual([], meta.get_model_field_info(CremeEntity, 'foobar'))
        self.assertEqual([], meta.get_model_field_info(CremeEntity, 'foo__bar'))

        #[{'field': <django.db.models.fields.related.ForeignKey object at ...>,
        #  'model': <class 'creme_core.models.creme_property.CremePropertyType'>}]
        with self.assertNoException():
            info = meta.get_model_field_info(CremeProperty, 'type')
            self.assertEqual(1, len(info))

            desc = info[0]
            self.assertIsInstance(desc['field'], fields.related.ForeignKey)
            self.assertEqual(CremePropertyType, desc['model'])

        #[{ 'field': <django.db.models.fields.related.ForeignKey object at ...>,
        #   'model': <class 'creme_core.models.creme_property.CremePropertyType'>},
        # {'field': <django.db.models.fields.CharField object at ...>,
        #   'model': None}]
        with self.assertNoException():
            info = meta.get_model_field_info(CremeProperty, 'type__text')
            self.assertEqual(2, len(info))

            desc = info[0]
            self.assertIsInstance(desc['field'], fields.related.ForeignKey)
            self.assertEqual(CremePropertyType, desc['model'])

            desc = info[1]
            self.assertIsInstance(desc['field'], fields.CharField)
            self.assertIsNone(desc['model'])

        #[{'field': <django.db.models.fields.related.ForeignKey object at 0x9d123ec>,
        #  'model': <class 'creme_core.models.entity.CremeEntity'>},
        # {'field': <django.db.models.fields.related.ForeignKey object at 0x9d0378c>,
        #  'model': <class 'django.contrib.contenttypes.models.ContentType'>},
        # {'field': <django.db.models.fields.CharField object at 0x99d302c>,
        #  'model': None}]
        with self.assertNoException():
            info = meta.get_model_field_info(CremeProperty, 'creme_entity__entity_type__name')
            self.assertEqual(3, len(info))

            desc = info[0]
            self.assertIsInstance(desc['field'], fields.related.ForeignKey)
            self.assertEqual(CremeEntity, desc['model'])

            desc = info[1]
            self.assertIsInstance(desc['field'], fields.related.ForeignKey)
            self.assertEqual(ContentType, desc['model'])

            desc = info[2]
            self.assertIsInstance(desc['field'], fields.CharField)
            self.assertIsNone(desc['model'])

    def test_get_model_field_info02(self):
        with self.assertNoException():
            info = meta.get_model_field_info(CremeProperty, 'type', silent=False)
            self.assertEqual(1, len(info))

            desc = info[0]
            self.assertIsInstance(desc['field'], fields.related.ForeignKey)
            self.assertEqual(CremePropertyType, desc['model'])

        with self.assertRaises(FieldDoesNotExist):
            meta.get_model_field_info(CremeEntity, 'foobar', silent=False)

        with self.assertRaises(FieldDoesNotExist):
            meta.get_model_field_info(CremeEntity, 'foo__bar', silent=False)

    def test_get_verbose_field_name(self):
        gvfn = meta.get_verbose_field_name
        self.assertEqual(_('First name'), gvfn(Contact,      'first_name'))
        self.assertEqual(_('Last name'),  gvfn(Contact,      'last_name'))
        self.assertEqual(_('Name'),       gvfn(Organisation, 'name'))

        self.assertEqual(_('Photograph') + ' - ' + _('Name'), gvfn(Contact, 'image__name'))
        self.assertEqual(_('Photograph') + '/'   + _('Name'), gvfn(Contact, 'image__name', separator='/'))

        self.assertEqual('', gvfn(Contact, 'stuff'))
        with self.assertRaises(FieldDoesNotExist):
            gvfn(Contact, 'stuff', silent=False)

        self.assertEqual(_('Photograph'), gvfn(Contact, 'image__stuff')) #'silent=True' is legacy mode but should be removed...
        with self.assertRaises(FieldDoesNotExist):
            gvfn(Contact, 'image__stuff', silent=False)

    def test_field_info01(self):
        "Simple field"
        fi = meta.FieldInfo(Contact, 'first_name')

        self.assertEqual(1, len(fi))

        with self.assertNoException():
            base_field = fi[0]

        #self.assertIsInstance(base_field, fields.CharField)
        #self.assertEqual('first_name', base_field.name)
        self.assertEqual(Contact._meta.get_field('first_name'), base_field)

        self.assertEqual(Organisation._meta.get_field('name'),
                         meta.FieldInfo(Organisation, 'name')[0]
                        )

        #FK
        self.assertEqual(Contact._meta.get_field('image'),
                         meta.FieldInfo(Contact, 'image')[0]
                        )

    def test_field_info02(self):
        "depth > 1"
        fi = meta.FieldInfo(Contact, 'image__name')

        self.assertEqual(2, len(fi))
        self.assertEqual(Contact._meta.get_field('image'), fi[0])
        self.assertEqual(Image._meta.get_field('name'),    fi[1])

        self.assertEqual(_('Photograph') + ' - ' + _('Name'), fi.verbose_name)

        with self.assertNoException():
            fi_as_list = list(meta.FieldInfo(Contact, 'image__user__username'))

        self.assertEqual([Contact._meta.get_field('image'),
                          Image._meta.get_field('user'),
                          get_user_model()._meta.get_field('username'),
                         ],
                         fi_as_list
                        )

    def test_field_info03(self):
        "Invalid fields"
        with self.assertRaises(FieldDoesNotExist):
            meta.FieldInfo(Contact, 'invalid')

        with self.assertRaises(FieldDoesNotExist):
            meta.FieldInfo(Contact, 'image__invalid')

        with self.assertRaises(FieldDoesNotExist):
            meta.FieldInfo(Contact, 'invalid__invalidtoo')

    def test_field_info04(self):
        "Slice"
        fi = meta.FieldInfo(Contact, 'image__user__username')

        with self.assertNoException():
            sub_fi = fi[1:]

        self.assertIsInstance(sub_fi, meta.FieldInfo)
        self.assertEqual(2, len(sub_fi))
        self.assertEqual(Image._meta.get_field('user'),    sub_fi[0])
        self.assertEqual(get_user_model()._meta.get_field('username'), sub_fi[1])

    def test_get_related_field(self):
        self.assertIsNone(meta.get_related_field(Contact, 'stuffes'))

        rf = meta.get_related_field(Contact, 'cremeproperty')
        self.assertEqual(CremeProperty, rf.model)
        self.assertEqual('properties',  rf.get_accessor_name())

    def test_get_date_fields(self):
        datefields = meta.get_date_fields(CremeEntity())
        self.assertEqual(2, len(datefields))
        self.assertEqual({'created', 'modified'}, {f.name for f in datefields})

    def test_is_date_field(self):
        entity = CremeEntity()
        get_field = entity._meta.get_field
        self.assertTrue(meta.is_date_field(get_field('created')))
        self.assertFalse(meta.is_date_field(get_field('user')))

    def test_field_enumerator01(self):
        expected = [('id',                         'ID'),
                    ('created',                    _('Creation date')),
                    ('modified',                   _('Last modification')),
                    #('entity_type',                'entity type'),
                    ('header_filter_search_field', 'header filter search field'),
                    ('is_deleted',                 'is deleted'),
                    ('is_actived',                 'is actived'),
                    #('user',                       _('User')),
                   ]
        choices = meta.ModelFieldEnumerator(CremeEntity).choices()
        self.assertEqual(expected, choices, choices)

        choices = meta.ModelFieldEnumerator(CremeEntity, only_leafs=True).choices()
        self.assertEqual(expected, choices, choices)

        choices = meta.ModelFieldEnumerator(CremeEntity, only_leafs=False).choices()
        self.assertEqual([('id',                         'ID'),
                          ('created',                    _('Creation date')),
                          ('modified',                   _('Last modification')),
                          ('entity_type',                'entity type'),
                          ('header_filter_search_field', 'header filter search field'),
                          ('is_deleted',                 'is deleted'),
                          ('is_actived',                 'is actived'),
                          #('user',                       _('User')),
                          ('user',                       _('Owner user')),
                         ],
                         choices, choices
                        )

    def test_field_enumerator02(self):
        "Filter, exclude (simple)"
        expected = [('created',  _('Creation date')),
                    ('modified', _('Last modification')),
                    #('user',     _('User'))
                   ]
        choices = meta.ModelFieldEnumerator(CremeEntity).filter(viewable=True).choices()
        self.assertEqual(expected, choices, choices)

        choices = meta.ModelFieldEnumerator(CremeEntity).exclude(viewable=False).choices()
        self.assertEqual(expected, choices, choices)

        expected = [('created',  _('Creation date')),
                    ('modified', _('Last modification')),
                    #('user',     _('User'))
                    ('user',     _('Owner user'))
                   ]
        choices = meta.ModelFieldEnumerator(CremeEntity, only_leafs=False).filter(viewable=True).choices()
        self.assertEqual(expected, choices, choices)

        choices = meta.ModelFieldEnumerator(CremeEntity, only_leafs=False).exclude(viewable=False).choices()
        self.assertEqual(expected, choices, choices)

    def test_field_enumerator03(self):
        "deep = 1"
        #fs = u'[%s] - %%s' % _('User')
        fs = u'[%s] - %%s' % _('Owner user')
        expected = [('created',          _('Creation date')),
                    ('modified',         _('Last modification')),
                    #('user',             _('User')),
                    ('user__username',   fs % _('Username')),
                    #('user__first_name', fs % _('first name')),
                    ('user__last_name',  fs % _('Last name')),
                    ('user__email',      fs % _('Email address')),
                    #('user__role',       fs % _('Role')),
                    #('user__is_team',    fs % _('Is a team ?')),
                   ]
        self.assertEqual(expected, meta.ModelFieldEnumerator(CremeEntity, deep=1).filter(viewable=True).choices())
        self.assertEqual(expected, meta.ModelFieldEnumerator(CremeEntity, deep=1, only_leafs=True).filter(viewable=True).choices())
        self.assertEqual(meta.ModelFieldEnumerator(CremeEntity, deep=1, only_leafs=False).filter(viewable=True).choices(),
                         [('created',          _('Creation date')),
                          ('modified',         _('Last modification')),
                          #('user',             _('User')),
                          ('user',             _('Owner user')),
                          ('user__username',   fs % _('Username')),
                          #('user__first_name', fs % _('first name')),
                          ('user__last_name',  fs % _('Last name')),
                          ('user__email',      fs % _('Email address')),
                          #('user__role',       fs % _('Role')),
                          #('user__is_team',    fs % _('Is a team ?')),
                         ]
                        )

    def test_field_enumerator04(self):
        "Filter with function, exclude"
        self.assertEqual(meta.ModelFieldEnumerator(CremeEntity, deep=1)
                             .filter(lambda f, depth: f.name.endswith('ied'), viewable=True)
                             .choices(),
                         [('modified', _('Last modification'))]
                        )
        self.assertEqual(meta.ModelFieldEnumerator(CremeEntity, deep=0)
                             .exclude(lambda f, depth: f.name.endswith('ied'), viewable=False)
                             .choices(),
                         [('created',  _('Creation date')),
                          #('user',     _('User')),
                         ]
                        )

#    @skipIfNotInstalled('creme.emails')
    def test_field_enumerator05(self):
        "Other ct"
#        from creme.emails.models import EmailCampaign

        expected = [('created',     _('Creation date')),
                    ('modified',    _('Last modification')),
                    ('name',        _('Name of the campaign')),
                   ]
        choices = meta.ModelFieldEnumerator(EmailCampaign).filter(viewable=True).choices()
        self.assertEqual(expected, choices, choices)

        choices = meta.ModelFieldEnumerator(EmailCampaign, only_leafs=False) \
                      .filter((lambda f, depth: f.get_internal_type() != 'ForeignKey'), viewable=True) \
                      .choices()

        expected.append(('mailing_lists', _('Related mailing lists')))
        self.assertEqual(expected, choices, choices)

    def test_field_enumerator06(self):
        "Filter/exclude : multiple conditions + field true attributes"
        expected = [('user',             _('Owner user')),
                    ('civility',         _('Civility')),
                    ('last_name',        _('Last name')),
                    ('first_name',       _('First name')),
                    ('is_a_nerd',        _(u'Is a Nerd')),
                    ('description',      _('Description')),
#                    ('skype',            _('Skype')),
                    ('phone',            _('Phone number')),
                    ('mobile',           _('Mobile')),
#                    ('fax',              _('Fax')),
                    ('position',         _('Position')),
                    ('sector',           _('Line of business')),
                    ('email',            _('Email address')),
                    ('url_site',         _('Web Site')),
                    ('birthday',         _('Birthday')),
                    ('image',            _('Photograph')),
                    ('languages',        _(u'Spoken language(s)')),
                   ]
        choices = meta.ModelFieldEnumerator(Contact, only_leafs=False) \
                      .filter(editable=True, viewable=True).choices()
        self.assertEqual(expected, choices, choices)

        choices = meta.ModelFieldEnumerator(Contact, only_leafs=False) \
                      .exclude(editable=False, viewable=False).choices()
        self.assertEqual(expected, choices, choices)

#    @skipIfNotInstalled('creme.tickets')
    def test_field_enumerator07(self):
        "Ordering of FKs"
#        from creme.tickets.models import Ticket
#
#        choices = meta.ModelFieldEnumerator(Ticket, deep=1, only_leafs=False).filter(viewable=True).choices()
#        fs = u'[%s] - %s'
#        user_lbl = _('Owner user')
#        self.assertEqual([('created',           _('Creation date')),
#                          ('modified',          _('Last modification')),
#                          ('user',              user_lbl),
#                          ('title',             _('Title')),
#                          ('description',       _('Description')),
#                          ('status',            _('Status')),
#                          ('priority',          _('Priority')),
#                          ('criticity',         _('Criticity')),
#                          ('solution',          _('Solution')),
#                          ('closing_date',      _('Closing date')),
#                          ('user__username',    fs % (user_lbl, _('Username'))),
#                          ('user__last_name',   fs % (user_lbl, _('Last name'))),
#                          ('user__email',       fs % (user_lbl, _('Email address'))),
#                          ('status__name',      fs % (_('Status'), _('Name'))),
#                          ('priority__name',    fs % (_('Priority'), _('Name'))),
#                          ('criticity__name',   fs % (_('Criticity'), _('Name'))),
#                         ],
#                         choices, choices
#                        )

        choices = meta.ModelFieldEnumerator(FakeActivity, deep=1, only_leafs=False) \
                      .filter(viewable=True).choices()
        fs = u'[%s] - %s'
        user_lbl = _('Owner user')
        type_lbl = _(u'Activity type')
        self.assertEqual([('created',           _('Creation date')),
                          ('modified',          _('Last modification')),
                          ('user',              user_lbl),
                          ('title',             _(u'Title')),
                          ('start',             _(u'Start')),
                          ('end',               _(u'End')),
                          ('type',              type_lbl),
                          ('user__username',    fs % (user_lbl, _('Username'))),
                          ('user__last_name',   fs % (user_lbl, _('Last name'))),
                          ('user__email',       fs % (user_lbl, _('Email address'))),
                          ('type__name',        fs % (type_lbl, _('Name')))
                         ],
                         choices, choices
                        )

#    @skipIfNotInstalled('creme.tickets')
    def test_field_enumerator08(self):
        "'depth' argument"
#        from creme.tickets.models import Ticket
#
#        choices = meta.ModelFieldEnumerator(Ticket, deep=1, only_leafs=False) \
#                      .filter((lambda f, depth: not depth or f.name == 'name'), viewable=True) \
#                      .choices()
#
#        fs = u'[%s] - %s'
#        self.assertEqual([('created',           _('Creation date')),
#                          ('modified',          _('Last modification')),
#                          ('user',              _('Owner user')),
#                          ('title',             _('Title')),
#                          ('description',       _('Description')),
#                          ('status',            _('Status')),
#                          ('priority',          _('Priority')),
#                          ('criticity',         _('Criticity')),
#                          ('solution',          _('Solution')),
#                          ('closing_date',      _('Closing date')),
#                          #('user__username',    fs % (user_lbl, _('username'))),
#                          #('user__first_name',  fs % (user_lbl, _('first name'))),
#                          # ...
#                          ('status__name',      fs % (_('Status'), _('Name'))),
#                          ('priority__name',    fs % (_('Priority'), _('Name'))),
#                          ('criticity__name',   fs % (_('Criticity'), _('Name'))),
#                         ],
#                         choices, choices
#                        )
        choices = meta.ModelFieldEnumerator(FakeActivity, deep=1, only_leafs=False) \
                      .filter((lambda f, depth: not depth or f.name == 'name'), viewable=True) \
                      .choices()

        fs = u'[%s] - %s'
        type_lbl = _(u'Activity type')
        self.assertEqual([('created',           _('Creation date')),
                          ('modified',          _('Last modification')),
                          ('user',              _('Owner user')),
                          ('title',             _(u'Title')),
                          ('start',             _(u'Start')),
                          ('end',               _(u'End')),
                          ('type',              type_lbl),
                          #('user__username',    fs % (user_lbl, _('Username'))),
                          #('user__last_name',   fs % (user_lbl, _('Last name'))),
                          #('user__email',       fs % (user_lbl, _('Email address'))),
                          ('type__name',        fs % (type_lbl, _('Name')))
                         ],
                         choices, choices
                        )
