# -*- coding: utf-8 -*-

try:
    from functools import partial
    from json import loads as load_json

    from django.contrib.contenttypes.models import ContentType
    from django.http import Http404
    from django.utils.translation import ugettext as _

    from .base import ViewsTestCase
#    from ..base import skipIfNotInstalled
    from ..fake_models import (FakeContact as Contact,
            FakeOrganisation as Organisation, FakeActivity, FakeImage)
    from creme.creme_core.auth.entity_credentials import EntityCredentials
    from creme.creme_core.models import (RelationType, SemiFixedRelationType,
            Relation, CremeEntity, CremePropertyType, CremeProperty)

#    from creme.persons.constants import REL_OBJ_CUSTOMER_SUPPLIER
#    from creme.persons.models import Contact, Organisation
except Exception as e:
    print('Error in <%s>: %s' % (__name__, e))


class RelationViewsTestCase(ViewsTestCase):
    DELETE_ALL_URL    = '/creme_core/relation/delete/all'
    ADD_FROM_PRED_URL = '/creme_core/relation/add_from_predicate/save'

    format_str    = '[{"rtype": "%s", "ctype": "%s", "entity": "%s"}]'
    format_str_2x = '[{"rtype": "%s", "ctype": "%s", "entity": "%s"},' \
                    ' {"rtype": "%s", "ctype": "%s", "entity": "%s"}]'
    format_str_3x = '[{"rtype": "%s", "ctype": "%s", "entity": "%s"},' \
                    ' {"rtype": "%s", "ctype": "%s", "entity": "%s"},' \
                    ' {"rtype": "%s", "ctype": "%s", "entity": "%s"}]'

    @classmethod
    def setUpClass(cls):
        ViewsTestCase.setUpClass()
#        cls.populate('creme_core', 'persons')
        cls.populate('creme_core')

    def _build_get_ctypes_url(self, rtype_id):
        return '/creme_core/relation/type/%s/content_types/json' % rtype_id

    def _build_predicates_json_url(self, entity):
        return '/creme_core/relation/entity/%s/rtypes/json' % entity.id

    def test_get_ctypes_of_relation01(self):
        'No sort'
        self.login()

        rtype = RelationType.create(('test-subject__JSP01_3', u'is a customer of', [Contact]),
                                    ('test-object__JSP01_4',  u'is a supplier of', [Contact, Organisation]),
                                   )[0]

#        response = self.assertGET200(self._build_get_ctypes_url(REL_OBJ_CUSTOMER_SUPPLIER),
        response = self.assertGET200(self._build_get_ctypes_url(rtype.id),
                                     data={'fields': ['id', 'unicode']}
                                    )
        self.assertEqual('text/javascript', response['Content-Type'])

        json_data = load_json(response.content)
        get_ct = ContentType.objects.get_for_model
#        self.assertEqual(json_data, [[get_ct(Contact).id,      Contact._meta.verbose_name],
#                                     [get_ct(Organisation).id, Organisation._meta.verbose_name],
#                                    ]
#                        )
        self.assertIsInstance(json_data, list)
        self.assertEqual(2, len(json_data))
        self.assertIn([get_ct(Contact).id,      unicode(Contact._meta.verbose_name)],      json_data)
        self.assertIn([get_ct(Organisation).id, unicode(Organisation._meta.verbose_name)], json_data)

#    @skipIfNotInstalled('creme.tickets')
    def test_get_ctypes_of_relation02(self):
#        from creme.tickets.models import Ticket
        self.login()

        rtype = RelationType.create(('test-subject_foobar1', 'is loving'),
                                    ('test-object_foobar1',  'is loved by')
                                   )[0]
        response = self.assertGET200(self._build_get_ctypes_url(rtype.id),
                                     data={'fields': ['id']}
                                    )
        self.assertEqual('text/javascript', response['Content-Type'])

        json_data = load_json(response.content)
        get_ct = ContentType.objects.get_for_model
        self.assertIn([get_ct(Contact).id], json_data)
        self.assertIn([get_ct(Organisation).id], json_data)
#        self.assertIn([get_ct(Ticket).id], json_data)
        self.assertIn([get_ct(FakeActivity).id], json_data)

    def test_get_ctypes_of_relation03(self):
        "'sort' argument"
        self.login()

        rtype = RelationType.create(('test-subject_foobar', 'foo'),
                                    ('test-object_foobar',  'bar', [FakeImage, Contact])
                                   )[0]

        response = self.assertGET200(self._build_get_ctypes_url(rtype.id),
                                     data={'fields': ['id', 'unicode'],
                                           'sort':   'unicode',
                                          },
                                    )

        c_vname = unicode(Contact._meta.verbose_name)
        i_vname = unicode(FakeImage._meta.verbose_name)
        get_ct = ContentType.objects.get_for_model

        expected = [[get_ct(Contact).id, c_vname]]
        expected.insert(0 if i_vname < c_vname else 1,
                        [get_ct(FakeImage).id,  i_vname]
                       )
        self.assertEqual(load_json(response.content), expected)

    def _aux_test_add_relations(self, is_superuser=True):
        user = self.login(is_superuser)

#        create_entity = lambda : CremeEntity.objects.create(user=self.user)
#        self.subject01 = create_entity()
#        self.subject02 = create_entity()
#        self.object01  = create_entity()
#        self.object02  = create_entity()
        create_contact = partial(Contact.objects.create, user=user)
        self.subject01 = create_contact(first_name='Laharl', last_name='Overlord')
        self.subject02 = create_contact(first_name='Etna',   last_name='Devil')

        create_orga = partial(Organisation.objects.create, user=user)
        self.object01 = create_orga(name='orga01')
        self.object02 = create_orga(name='orga02')

        self.ct_id = ContentType.objects.get_for_model(CremeEntity).id

        self.rtype01 = RelationType.create(('test-subject_foobar1', 'is loving'),
                                           ('test-object_foobar1',  'is loved by')
                                          )[0]
        self.rtype02 = RelationType.create(('test-subject_foobar2', 'is hating'),
                                           ('test-object_foobar2',  'is hated by')
                                          )[0]

    def assertEntiTyHasRelation(self, subject_entity, rtype, object_entity):
        self.assertTrue(subject_entity.relations
                                      .filter(type=rtype, object_entity=object_entity.id)
                                      .exists()
                       )

    def _build_add_url(self, subject):
        return '/creme_core/relation/add/%s' % subject.id

    def count_relations(self, rtype):
        return Relation.objects.filter(type=rtype).count()

    def assert_relation_count(self, counts):
        assertEqual = self.assertEqual
        rcount = self.count_relations
        for rtype, count in counts:
            assertEqual(count, rcount(rtype))

    def test_add_relations01(self):
        self._aux_test_add_relations()

        subject = self.subject01
        self.assertFalse(subject.relations.all())

        url = self._build_add_url(subject)
        self.assertGET200(url)

        ct_id = self.ct_id
        response = self.client.post(url, data={'relations': self.format_str_2x % (
                                                                self.rtype01.id, ct_id, self.object01.id,
                                                                self.rtype02.id, ct_id, self.object02.id,
                                                              ),
                                              }
                                   )
        self.assertNoFormError(response)
        self.assertEqual(2, subject.relations.count())
        self.assertEntiTyHasRelation(subject, self.rtype01, self.object01)
        self.assertEntiTyHasRelation(subject, self.rtype02, self.object02)

    def test_add_relations02(self):
        "Credentials problems"
        self.login(is_superuser=False)
        subject = CremeEntity.objects.create(user=self.other_user)
        self.assertGET403(self._build_add_url(subject))

    def test_add_relations03(self):
        "Credentials problems (no link credentials)"
        self._aux_test_add_relations(is_superuser=False)
        self._set_all_creds_except_one(excluded=EntityCredentials.LINK)

        unlinkable = CremeEntity.objects.create(user=self.other_user)
        self.assertTrue(self.user.has_perm_to_view(unlinkable))
        self.assertFalse(self.user.has_perm_to_link(unlinkable))

        ct_id = self.ct_id
        response = self.client.post(self._build_add_url(self.subject01),
                                    data={'relations': self.format_str_2x % (
                                                                self.rtype01.id, ct_id, self.object01.id,
                                                                self.rtype02.id, ct_id, unlinkable.id,
                                                            ),
                                         }
                                   )
        self.assertFormError(response, 'form', 'relations',
                             _(u'Some entities are not linkable: %s') % unlinkable
                            )
        self.assertEqual(0, self.subject01.relations.count())

    def test_add_relations04(self):
        "Duplicates -> error"
        self._aux_test_add_relations()

        ct_id = self.ct_id
        response = self.client.post(self._build_add_url(self.subject01),
                                    data={'relations': self.format_str_3x % (
                                                            self.rtype01.id, ct_id, self.object01.id,
                                                            self.rtype02.id, ct_id, self.object02.id,
                                                            self.rtype01.id, ct_id, self.object01.id,
                                                        ),
                                         }
                                   )
        self.assertFormError(response, 'form', 'relations',
                             #_(u'There are duplicates: %s') % (u'(%s, %s)' % (self.rtype01, self.object01))
                             _(u'There are duplicates: %(duplicates)s') % {
                                 'duplicates': u'(%s, %s)' % (self.rtype01, self.object01),
                                 }
                            )

    def test_add_relations05(self):
        "Do not recreate existing relations"
        self._aux_test_add_relations()

        Relation.objects.create(user=self.user,
                                subject_entity=self.subject01,
                                type=self.rtype02,
                                object_entity=self.object02
                               )
        ct_id = self.ct_id
        response = self.client.post(self._build_add_url(self.subject01),
                                    data={'relations': self.format_str_2x % (
                                                            self.rtype01.id, ct_id, self.object01.id,
                                                            self.rtype02.id, ct_id, self.object02.id,
                                                        ),
                                          }
                                   )
        self.assertNoFormError(response)
        self.assertEqual(2, self.subject01.relations.count()) #and not 3

    def test_add_relations06(self):
        "Can not link an entity to itself"
        self._aux_test_add_relations()

        subject = self.subject01
        response = self.client.post(self._build_add_url(subject),
                                    data={'relations': self.format_str % (
                                                            self.rtype01.id, self.ct_id, subject.id
                                                        ),
                                         }
                                   )
        self.assertFormError(response, 'form', 'relations',
                             #_(u'An entity can not be linked to itself : %s') % subject
                             _(u'An entity can not be linked to itself : %(entities)s') % {
                                    'entities': subject,
                                }
                            )

    def test_add_relations_with_semi_fixed01(self):
        "Only semi fixed"
        self._aux_test_add_relations()

        subject = self.subject01

        # Contraint OK & KO
        create_rtype = RelationType.create
        rtype03 = create_rtype(('test-subject_foobar3', 'is hating orga',     [Contact]),
                               ('test-object_foobar3',  '(orga) is hated by', [Organisation]),
                              )[0]
        rtype04 = create_rtype(('test-subject_foobar4', 'has fired', [Organisation]), # subject cannot be a Contact
                               ('test-object_foobar4',  'has been fired by')
                              )[0]

        create_sfrt = SemiFixedRelationType.objects.create
        sfrt1 = create_sfrt(predicate='Related to "object01"',
                            relation_type=self.rtype01, object_entity=self.object01,
                           )
        sfrt2 = create_sfrt(predicate='Related to "object02"',
                            relation_type=self.rtype02, object_entity=self.object02,
                           )
        sfrt3 = create_sfrt(predicate='Linked to "object02"',
                            relation_type=rtype03, object_entity=self.object02,
                           )
        create_sfrt(predicate='Linked to "object01"',
                            relation_type=rtype04, object_entity=self.object01,
                           ) # should not be proposed

        url = self._build_add_url(subject)

        with self.assertNoException():
            semifixed_rtypes = self.client.get(url).context['form'].fields['semifixed_rtypes']

        self.assertEqual([(sfrt1.id, sfrt1.predicate),
                          (sfrt2.id, sfrt2.predicate),
                          (sfrt3.id, sfrt3.predicate),
                         ],
                         list(semifixed_rtypes.choices)
                        )

        self.assertNoFormError(self.client.post(url, data={'semifixed_rtypes': [sfrt1.id, sfrt2.id]}))
        self.assertEqual(2, subject.relations.count())
        self.assertEntiTyHasRelation(subject, self.rtype01, self.object01)
        self.assertEntiTyHasRelation(subject, self.rtype02, self.object02)

    def test_add_relations_with_semi_fixed02(self):
        "Semi-fixed & not semi-fixed"
        self._aux_test_add_relations()

        subject = self.subject01

        create_sfrt = SemiFixedRelationType.objects.create
        sfrt1 = create_sfrt(predicate='Related to "object01"',
                            relation_type=self.rtype01, object_entity=self.object01,
                           )
        sfrt2 = create_sfrt(predicate='Related to "object02"',
                            relation_type=self.rtype02, object_entity=self.object02,
                           )
        create_sfrt(predicate='Related to "subject01"',
                    relation_type=self.rtype02, object_entity=self.subject01,
                   ) #should not be proposed

        url = self._build_add_url(subject)
        context = self.client.get(url).context

        with self.assertNoException():
            field_sfrt = context['form'].fields['semifixed_rtypes']

        self.assertEqual({sfrt1.id, sfrt2.id},
                         {pk for pk, sfrt in field_sfrt.choices}
                        )

        response = self.client.post(url, data={'relations': self.format_str % (
                                                                self.rtype01.id,
                                                                self.ct_id,
                                                                self.object01.id,
                                                             ),
                                               'semifixed_rtypes': [sfrt2.id],
                                              }
                                   )
        self.assertNoFormError(response)
        self.assertEqual(2, subject.relations.count())
        self.assertEntiTyHasRelation(subject, self.rtype01, self.object01)
        self.assertEntiTyHasRelation(subject, self.rtype02, self.object02)

    def test_add_relations_with_semi_fixed03(self):
        "One relationship at least (semi-fixed or not semi-fixed)"
        self._aux_test_add_relations()

        response = self.assertPOST200(self._build_add_url(self.subject01))
        self.assertFormError(response, 'form', None,
                             _(u'You must give one relationship at least.')
                            )

    def test_add_relations_with_semi_fixed04(self):
        "Collision fixed / not fixed"
        self._aux_test_add_relations()

        subject = self.subject01

        create_sfrt = SemiFixedRelationType.objects.create
        sfrt1 = create_sfrt(predicate='Related to "object01"',
                            relation_type=self.rtype01, object_entity=self.object01,
                           )
        sfrt2 = create_sfrt(predicate='Related to "object02"',
                            relation_type=self.rtype02, object_entity=self.object02,
                           )

        response = self.client.post(self._build_add_url(subject),
                                    data={'relations': self.format_str % (
                                                            self.rtype01.id, self.ct_id, self.object01.id,
                                                        ),
                                          'semifixed_rtypes': [sfrt1.id, sfrt2.id],
                                         }
                                   )
        self.assertFormError(response, 'form', None,
                             #_(u'There are duplicates: %s') % (u'(%s, %s)' % (self.rtype01, self.object01))
                             _(u'There are duplicates: %(duplicates)s') % {
                                    'duplicates': u'(%s, %s)' % (self.rtype01, self.object01),
                                 }
                            )

    def test_add_relations_with_semi_fixed05(self):
        "Filter not linkable entities"
        self._aux_test_add_relations(is_superuser=False)
        self._set_all_creds_except_one(excluded=EntityCredentials.LINK)

        unlinkable = CremeEntity.objects.create(user=self.other_user)

        create_sfrt = SemiFixedRelationType.objects.create
        create_sfrt(predicate='Related to "unlinkable"',
                    relation_type=self.rtype01, object_entity=unlinkable, # <===
                   )
        sfrt2 = create_sfrt(predicate='Related to "object02"',
                            relation_type=self.rtype02, object_entity=self.object02,
                           )

        response = self.assertGET200('/creme_core/relation/add/%s' % self.subject01.id)

        with self.assertNoException():
            sfrt_field = response.context['form'].fields['semifixed_rtypes']

        self.assertEqual([(sfrt2.id, sfrt2.predicate)], list(sfrt_field.choices))

    def _build_narrowed_add_url(self, subject, rtype):
        return '/creme_core/relation/add/%s/%s' % (subject.id, rtype.id)

    def test_add_relations_narrowedtype01(self):
        self._aux_test_add_relations()

        rtype = self.rtype01
        subject = self.subject01
        url = self._build_narrowed_add_url(subject, rtype)
        self.assertGET200(url)

        ct_id = self.ct_id
        response = self.client.post(url, data={'relations': self.format_str_2x % (
                                                                rtype.id, ct_id, self.object01.id,
                                                                rtype.id, ct_id, self.object02.id,
                                                             ),
                                              }
                                   )
        self.assertNoFormError(response)
        self.assertEqual(2, subject.relations.count())
        self.assertEntiTyHasRelation(subject, rtype, self.object01)
        self.assertEntiTyHasRelation(subject, rtype, self.object02)

    def test_add_relations_narrowedtype02(self):
        "Validation error"
        self._aux_test_add_relations()

        ct_id = self.ct_id
        response = self.client.post(self._build_narrowed_add_url(self.subject01, self.rtype01),
                                    data={'relations': self.format_str_2x % (
                                                                self.rtype01.id, ct_id, self.object01.id,
                                                                self.rtype02.id, ct_id, self.object02.id, #rtype not allowed
                                                            ),
                                         }
                                   )
        self.assertFormError(response, 'form', 'relations',
                             _(u'This type of relationship causes a constraint error.')
                            )

    def test_add_relations_narrowedtype03(self):
        self._aux_test_add_relations()

        allowed_rtype = self.rtype01
        subject = self.subject01

        create_sfrt = SemiFixedRelationType.objects.create
        sfrt1 = create_sfrt(predicate='Related to "object01"',
                            relation_type=allowed_rtype, object_entity=self.object01,
                           )
        create_sfrt(predicate='Related to "object02"',
                    relation_type=self.rtype02, object_entity=self.object02,
                   )

        url = self._build_narrowed_add_url(subject, allowed_rtype)

        with self.assertNoException():
            sfrt_field = self.client.get(url).context['form'].fields['semifixed_rtypes']

        self.assertEqual([(sfrt1.id, sfrt1.predicate)], list(sfrt_field.choices))

        response = self.client.post(url, data={'relations': self.format_str % (
                                                                allowed_rtype.id, self.ct_id, self.object02.id,
                                                              ),
                                                'semifixed_rtypes': [sfrt1.id],
                                              }
                                   )
        self.assertNoFormError(response)
        self.assertEqual(2, subject.relations.count())
        self.assertEntiTyHasRelation(subject, allowed_rtype, self.object01)
        self.assertEntiTyHasRelation(subject, allowed_rtype, self.object02)

    def _build_bulk_add_url(self, ct_id, *subjects):
        return '/creme_core/relation/add_to_entities/%(ct_id)s/?%(sub_ids)s&persist=ids' % {
                        'ct_id':   ct_id,
                        'sub_ids': ''.join('ids=%s&' % subject.id for subject in subjects),
                    }

    def test_add_relations_bulk01(self):
        self._aux_test_add_relations()

        #this relation should not be recreated by the view
        Relation.objects.create(user=self.user,
                                subject_entity=self.subject02,
                                type=self.rtype02,
                                object_entity=self.object02
                               )
        ct_id = self.ct_id
        url = self._build_bulk_add_url(ct_id, self.subject01, self.subject02)
        self.assertGET200(url)

        response = self.client.post(url, data={'entities_lbl': 'wtf',
                                               'relations':    self.format_str_2x % (
                                                                    self.rtype01.id, ct_id, self.object01.id,
                                                                    self.rtype02.id, ct_id, self.object02.id,
                                                                ),
                                              })
        self.assertNoFormError(response)

        self.assertEqual(2, self.subject01.relations.count())
        self.assertEntiTyHasRelation(self.subject01, self.rtype01, self.object01)
        self.assertEntiTyHasRelation(self.subject01, self.rtype02, self.object02)

        self.assertEqual(2, self.subject02.relations.count()) #and not 3
        self.assertEntiTyHasRelation(self.subject02, self.rtype01, self.object01)
        self.assertEntiTyHasRelation(self.subject02, self.rtype02, self.object02)

    def test_add_relations_bulk02(self):
        self._aux_test_add_relations(is_superuser=False)

        unviewable = CremeEntity.objects.create(user=self.other_user)
        self.assertFalse(self.user.has_perm_to_view(unviewable))

        url = self._build_bulk_add_url(self.ct_id, self.subject01, unviewable)
        response = self.assertGET200(url)

        with self.assertNoException():
            label = response.context['form'].fields['bad_entities_lbl']

        self.assertTrue(label.initial)

        ct_id = self.ct_id
        response = self.client.post(url, data={'entities_lbl':     'do not care',
                                               'bad_entities_lbl': 'do not care',
                                               'relations':        self.format_str_2x % (
                                                                        self.rtype01.id, ct_id, self.object01.id,
                                                                        self.rtype02.id, ct_id, self.object02.id,
                                                                    ),
                                              })
        self.assertNoFormError(response)
        self.assertEqual(2, self.subject01.relations.count())
        self.assertEqual(0, unviewable.relations.count())

    def test_add_relations_bulk03(self):
        self._aux_test_add_relations(is_superuser=False)

        self._set_all_creds_except_one(excluded=EntityCredentials.LINK)
        unlinkable = CremeEntity.objects.create(user=self.other_user)
        self.assertTrue(self.user.has_perm_to_view(unlinkable))
        self.assertFalse(self.user.has_perm_to_link(unlinkable))

        response = self.assertGET200(self._build_bulk_add_url(self.ct_id, self.subject01, unlinkable))

        with self.assertNoException():
            label = response.context['form'].fields['bad_entities_lbl']

        self.assertEqual(unicode(unlinkable), label.initial)

    def test_add_relations_bulk04(self):
        self._aux_test_add_relations(is_superuser=False)

        url =  self._build_bulk_add_url(self.ct_id, self.subject01)
        self.assertGET200(url)

        self._set_all_creds_except_one(excluded=EntityCredentials.LINK)
        unlinkable = CremeEntity.objects.create(user=self.other_user)

        response = self.assertPOST200(url, data={'entities_lbl': 'wtf',
                                                 'relations':    self.format_str % (
                                                                    self.rtype01.id,
                                                                    self.ct_id,
                                                                    unlinkable.id
                                                                  ),
                                                }
                                     )
        self.assertFormError(response, 'form', 'relations',
                             _(u'Some entities are not linkable: %s') % unlinkable
                            )

    def test_add_relations_bulk05(self):
        "Can not link an entity to itself"
        self._aux_test_add_relations()

        ct_id = self.ct_id
        subject01 = self.subject01
        subject02 = self.subject02
        response = self.client.post(self._build_bulk_add_url(ct_id, subject01, subject02),
                                    data={'entities_lbl': 'wtf',
                                          'relations':    self.format_str_2x % (
                                                                self.rtype01.id, ct_id, subject01.id,
                                                                self.rtype02.id, ct_id, subject02.id,
                                                            ),
                                         }
                                   )
        self.assertFormError(response, 'form', 'relations',
                             #_(u'An entity can not be linked to itself : %s') % (
                                    #'%s, %s' % (subject01, subject02)
                                  #)
                            _(u'An entity can not be linked to itself : %(entities)s') % {
                                    'entities': '%s, %s' % (subject01, subject02),
                                  }
                            )

    def test_add_relations_bulk_with_semifixed01(self):
        self._aux_test_add_relations()

        #this relation should not be recreated by the view
        Relation.objects.create(user=self.user,
                                subject_entity=self.subject02,
                                type=self.rtype02,
                                object_entity=self.object02
                               )

        sfrt = SemiFixedRelationType.objects.create(predicate='Related to "object01"',
                                                    relation_type=self.rtype01,
                                                    object_entity=self.object01,
                                                   )

        response = self.client.post(self._build_bulk_add_url(self.ct_id, self.subject01, self.subject02),
                                    data={'entities_lbl':     'wtf',
                                          'relations':        self.format_str % (
                                                                  self.rtype02.id, self.ct_id, self.object02.id,
                                                                ),
                                          'semifixed_rtypes': [sfrt.id],
                                         }
                                   )
        self.assertNoFormError(response)

        self.assertEqual(2, self.subject01.relations.count())
        self.assertEntiTyHasRelation(self.subject01, self.rtype01, self.object01)
        self.assertEntiTyHasRelation(self.subject01, self.rtype02, self.object02)

        self.assertEqual(2, self.subject02.relations.count()) #and not 3
        self.assertEntiTyHasRelation(self.subject02, self.rtype01, self.object01)
        self.assertEntiTyHasRelation(self.subject02, self.rtype02, self.object02)

    def test_add_relations_bulk_fixedrtypes01(self):
        self._aux_test_add_relations()

        #this relation should not be recreated by the view
        Relation.objects.create(user=self.user,
                                subject_entity=self.subject02,
                                type=self.rtype02,
                                object_entity=self.object02
                               )

        url = '/creme_core/relation/add_to_entities/%s/%s,%s,/?ids=%s&ids=%s&persist=ids' % (
                    self.ct_id, self.rtype01.id, self.rtype02.id, self.subject01.id, self.subject02.id
                )
        self.assertGET200(url)

        ct_id = self.ct_id
        response = self.client.post(url, data={'entities_lbl': 'wtf',
                                               'relations':    self.format_str_2x % (
                                                                    self.rtype01.id, ct_id, self.object01.id,
                                                                    self.rtype02.id, ct_id, self.object02.id,
                                                                   ),
                                              })

        self.assertNoFormError(response)

        self.assertEqual(2, self.subject01.relations.count())
        self.assertEntiTyHasRelation(self.subject01, self.rtype01, self.object01)
        self.assertEntiTyHasRelation(self.subject01, self.rtype02, self.object02)

        self.assertEqual(2, self.subject02.relations.count()) #and not 3
        self.assertEntiTyHasRelation(self.subject02, self.rtype01, self.object01)
        self.assertEntiTyHasRelation(self.subject02, self.rtype02, self.object02)

    def test_add_relations_bulk_fixedrtypes02(self):
        self._aux_test_add_relations()

        url = '/creme_core/relation/add_to_entities/%s/%s/?ids=%s&ids=%s&persist=ids' % (
                    self.ct_id, self.rtype01.id, self.subject01.id, self.subject02.id
                )
        self.assertGET200(url)

        ct_id = self.ct_id
        response = self.assertPOST200(url, data={'entities_lbl': 'wtf',
                                                 'relations': self.format_str_2x % (
                                                                self.rtype02.id, ct_id, self.object01.id,
                                                                self.rtype02.id, ct_id, self.object02.id,
                                                               ),
                                                }
                                     )
        self.assertFormError(response, 'form', 'relations',
                             _(u'This type of relationship causes a constraint error.')
                            )

    def _aux_relation_objects_to_link_selection(self):
        user = self.login()

#        self.assertEqual(3, Contact.objects.count())
#        self.contact01 = Contact.objects.get(is_user=1)

        self.subject   = CremeEntity.objects.create(user=user)
#        self.contact02 = self.user.linked_contact
#        self.contact03 = self.other_user.linked_contact

        create_user = partial(Contact.objects.create, user=user)
        self.contact01 = create_user(first_name='Laharl', last_name='Overlord')
        self.contact02 = create_user(first_name='Etna',   last_name='Devil')
        self.contact03 = create_user(first_name='Flone',   last_name='Angel')

        self.orga01 = Organisation.objects.create(user=user, name='Earth Defense Force')

        self.ct_contact = ContentType.objects.get_for_model(Contact)

        self.rtype = RelationType.create(('test-subject_foobar', 'is loving',   [Contact]),
                                         ('test-object_foobar',  'is loved by', [Contact])
                                        )[0]

    def _build_selection_url(self, rtype, subject, ct):
        return '/creme_core/relation/objects2link/rtype/%s/entity/%s/%s' % (
                    rtype.id,
                    subject.id,
                    ct.id
                )

    def test_objects_to_link_selection01(self):
        self._aux_relation_objects_to_link_selection()

        response = self.assertGET200(self._build_selection_url(self.rtype, self.subject, self.ct_contact))

        #with self.assertNoException():
        try:
            entities = response.context['entities']
        except KeyError:
            self.fail(response.content)

        contacts = entities.object_list
        self.assertEqual(3, len(contacts))
        self.assertTrue(all(isinstance(c, Contact) for c in contacts))
        self.assertEqual({self.contact01, self.contact02, self.contact03}, set(contacts))

    def test_objects_to_link_selection02(self):
        self._aux_relation_objects_to_link_selection()

        #contact03 will not be proposed by the listview
        Relation.objects.create(user=self.user, type=self.rtype, subject_entity=self.subject, object_entity=self.contact03)

        response = self.assertGET200(self._build_selection_url(self.rtype, self.subject, self.ct_contact))

        contacts = response.context['entities'].object_list
        self.assertEqual(2, len(contacts))
        self.assertEqual({self.contact01, self.contact02}, set(contacts))

    def test_objects_to_link_selection03(self):
        self._aux_relation_objects_to_link_selection()

        create_ptype = CremePropertyType.create
        ptype01 = create_ptype(str_pk='test-prop_foobar01', text='Is lovable')
        ptype02 = create_ptype(str_pk='test-prop_foobar02', text='Is a girl')

        contact04 = Contact.objects.create(user=self.user, first_name='Flonne', last_name='Angel')

        #contact02 will not be proposed by the listview
        create_property = CremeProperty.objects.create
        create_property(type=ptype01, creme_entity=self.contact01)
        create_property(type=ptype02, creme_entity=self.contact03)
        create_property(type=ptype01, creme_entity=contact04)
        create_property(type=ptype02, creme_entity=contact04)

        rtype, sym_rtype = RelationType.create(('test-subject_loving', 'is loving',   [Contact]),
                                               ('test-object_loving',  'is loved by', [Contact], [ptype01, ptype02])
                                              )

        response = self.assertGET200(self._build_selection_url(rtype, self.subject, self.ct_contact))

        contacts = response.context['entities'].object_list
        self.assertEqual(3, len(contacts))
        self.assertEqual({self.contact01, self.contact03, contact04}, set(contacts))

    def test_objects_to_link_selection04(self):
        self.login()

        subject = CremeEntity.objects.create(user=self.user)
        ct = ContentType.objects.get_for_model(Contact)
        rtype = RelationType.create(('test-subject_foobar', 'is loving',   [Contact]),
                                    ('test-object_foobar',  'is loved by', [Contact]),
                                    is_internal=True
                                   )[0]

        self.assertGET404(self._build_selection_url(rtype, subject, ct))

    def _aux_add_relations_with_same_type(self):
        create_entity = lambda: CremeEntity.objects.create(user=self.user)
        self.subject  = create_entity()
        self.object01 = create_entity()
        self.object02 = create_entity()
        self.rtype = RelationType.create(('test-subject_foobar', 'is loving',),
                                         ('test-object_foobar',  'is loved by',)
                                        )[0]

    def test_add_relations_with_same_type01(self):
        "No error"
        self.login()
        self._aux_add_relations_with_same_type()

        object_ids = [self.object01.id, self.object02.id]
        self.assertPOST200(self.ADD_FROM_PRED_URL,
                           data={'subject_id':   self.subject.id,
                                 'predicate_id': self.rtype.id,
                                 'entities':     object_ids,
                                 }
                          )
        self.assertEqual(2, Relation.objects.filter(type=self.rtype).count())

        relations = self.subject.relations.filter(type=self.rtype)
        self.assertEqual(2, len(relations))
        self.assertEqual(set(object_ids), {r.object_entity_id for r in relations})

    def test_add_relations_with_same_type02(self):
        "An entity does not exist"
        self.login()
        self._aux_add_relations_with_same_type()

        self.assertPOST404(self.ADD_FROM_PRED_URL,
                           data={'subject_id':   self.subject.id,
                                 'predicate_id': self.rtype.id,
                                 'entities':     [self.object01.id,
                                                  self.object02.id,
                                                  self.object02.id + 1,
                                                 ],
                                }
                          )
        self.assertEqual(2, Relation.objects.filter(type=self.rtype).count())

    def test_add_relations_with_same_type03(self):
        "Errors"
        self.login()
        self._aux_add_relations_with_same_type()

        url = self.ADD_FROM_PRED_URL
        self.assertPOST404(url, data={'subject_id':    self.subject.id,
                                      'predicate_id': 'IDONOTEXIST',
                                      'entities':      [self.object01.id],
                                     }
                          )
        self.assertPOST404(url, data={'subject_id':   1024,
                                      'predicate_id': self.rtype.id,
                                      'entities':     [self.object01.id],
                                     }
                          )
        self.assertPOST404(url, data={'predicate_id': self.rtype.id,
                                      'entities':     [self.object01.id],
                                     }
                          )
        self.assertPOST404(url, data={'subject_id': self.subject.id,
                                      'entities':   [self.object01.id],
                                     }
                          )
        self.assertPOST404(url, data={'subject_id':   self.subject.id,
                                      'predicate_id': self.rtype.id,
                                     }
                          )

    def test_add_relations_with_same_type04(self):
        "Credentials errors"
        user = self.login(is_superuser=False)
        self._set_all_creds_except_one(excluded=EntityCredentials.LINK)

        create_entity = CremeEntity.objects.create
        forbidden = create_entity(user=self.other_user)
        allowed01 = create_entity(user=user)
        allowed02 = create_entity(user=user)

        rtype, sym_rtype = RelationType.create(('test-subject_foobar', 'is loving',),
                                               ('test-object_foobar',  'is loved by',)
                                              )

        self.assertFalse(user.has_perm_to_link(forbidden))
        self.assertTrue(user.has_perm_to_link(allowed01))

        self.assertPOST403(self.ADD_FROM_PRED_URL,
                           data={'subject_id':   forbidden.id,
                                 'predicate_id': rtype.id,
                                 'entities':     [allowed01.id, allowed02.id],
                                }

                          )
        self.assertFalse(Relation.objects.filter(type=rtype.id))

        self.assertPOST403(self.ADD_FROM_PRED_URL,
                           data={'subject_id':   allowed01.id,
                                 'predicate_id': rtype.id,
                                 'entities':     [forbidden.id, allowed02.id, 1024],
                                }
                        )
        relations = Relation.objects.filter(type=rtype)
        self.assertEqual(1, len(relations))

        relation = relations[0]
        self.assertEqual(allowed01, relation.subject_entity)
        self.assertEqual(allowed02, relation.object_entity)

    def test_add_relations_with_same_type05(self):
        "ContentType constraint errors"
        user = self.login()

        create_orga = partial(Organisation.objects.create, user=user)
        orga01 = create_orga(name='orga01')
        orga02 = create_orga(name='orga02')

        create_contact = partial(Contact.objects.create, user=user)
        contact01 = create_contact(first_name='John', last_name='Doe')
        contact02 = create_contact(first_name='Joe',  last_name='Gohn')

        rtype = RelationType.create(('test-subject_foobar', 'manages',       [Contact]),
                                    ('test-object_foobar',  'is managed by', [Organisation])
                                   )[0]

        self.assertPOST(409, self.ADD_FROM_PRED_URL,
                        data={'subject_id':   orga01.id,
                              'predicate_id': rtype.id,
                              'entities':     [orga02.id],
                             }
                        )
        self.assertFalse(Relation.objects.filter(type=rtype.id))

        self.assertPOST(409, self.ADD_FROM_PRED_URL,
                        data={'subject_id':   contact01.id,
                              'predicate_id': rtype.id,
                              'entities':     [orga01.id, contact02.id],
                             }
                       )
        relations = Relation.objects.filter(type=rtype)
        self.assertEqual(1,         len(relations))
        self.assertEqual(orga01.id, relations[0].object_entity_id)

    def test_add_relations_with_same_type06(self):
        "Property constraint errors"
        self.login()

        create_ptype = CremePropertyType.create
        subject_ptype = create_ptype(str_pk='test-prop_foobar01', text='Subject property')
        object_ptype  = create_ptype(str_pk='test-prop_foobar02', text='Contact property')

        create_entity = lambda: CremeEntity.objects.create(user=self.user)
        bad_subject  = create_entity()
        good_subject = create_entity()
        bad_object   = create_entity()
        good_object  = create_entity()

        CremeProperty.objects.create(type=subject_ptype, creme_entity=good_subject)
        CremeProperty.objects.create(type=object_ptype, creme_entity=good_object)

        rtype, sym_rtype = RelationType.create(('test-subject_foobar', 'manages',       [], [subject_ptype]),
                                               ('test-object_foobar',  'is managed by', [], [object_ptype])
                                              )

        self.assertPOST(409, self.ADD_FROM_PRED_URL,
                        data={'subject_id':   bad_subject.id,
                              'predicate_id': rtype.id,
                              'entities':     [good_object.id],
                             }
                        )
        self.assertFalse(Relation.objects.filter(type=rtype))

        self.assertPOST(409, self.ADD_FROM_PRED_URL,
                        data={'subject_id':   good_subject.id,
                              'predicate_id': rtype.id,
                              'entities':     [good_object.id, bad_object.id],
                             }
                        )
        relations = Relation.objects.filter(type=rtype)
        self.assertEqual(1,              len(relations))
        self.assertEqual(good_object.id, relations[0].object_entity_id)

    def test_add_relations_with_same_type07(self):
        "Is internal"
        self.login()

        create_entity = lambda: CremeEntity.objects.create(user=self.user)
        subject  = create_entity()
        object01 = create_entity()
        object02 = create_entity()
        rtype = RelationType.create(('test-subject_foobar', 'is loving',),
                                    ('test-object_foobar',  'is loved by',),
                                    is_internal=True
                                   )[0]
        self.assertPOST404(self.ADD_FROM_PRED_URL,
                           data={'subject_id':   subject.id,
                                 'predicate_id': rtype.id,
                                 'entities':     [object01.id, object02.id],
                                }
                          )
        self.assertFalse(Relation.objects.filter(type=rtype))

    def _delete(self, relation):
        return self.client.post('/creme_core/relation/delete', data={'id': relation.id})

    def test_delete01(self):
        user = self.login()

        create_entity = lambda: CremeEntity.objects.create(user=user)
        subject_entity = create_entity()
        object_entity  = create_entity()

        rtype = RelationType.create(('test-subject_foobar', 'is loving'),
                                    ('test-object_foobar',  'is loved by'),
                                   )[0]
        relation = Relation.objects.create(subject_entity=subject_entity, type=rtype,
                                           object_entity=object_entity, user=user,
                                          )
        sym_relation = relation.symmetric_relation
        self.assertIsNone(rtype.is_not_internal_or_die())

        self.assertEqual(302, self._delete(relation).status_code)
        self.assertFalse(Relation.objects.filter(pk__in=[relation.pk, sym_relation.pk]))

    def test_delete02(self):
        user = self.login(is_superuser=False)

        self._set_all_creds_except_one(excluded=EntityCredentials.UNLINK)

        allowed   = CremeEntity.objects.create(user=user)
        forbidden = CremeEntity.objects.create(user=self.other_user)
        rtype = RelationType.create(('test-subject_foobar', 'is loving'),
                                    ('test-object_foobar',  'is loved by'),
                                   )[0]

        create_rel = partial(Relation.objects.create, user=user, type=rtype)
        relation = create_rel(subject_entity=allowed, object_entity=forbidden)
        self.assertEqual(403, self._delete(relation).status_code)
        self.get_object_or_fail(Relation, pk=relation.pk)

        relation = create_rel(subject_entity=forbidden, object_entity=allowed)
        self.assertEqual(403, self._delete(relation).status_code)
        self.get_object_or_fail(Relation, pk=relation.pk)

    def test_delete03(self):
        "Is internal"
        user = self.login()

        create_entity = partial(CremeEntity.objects.create, user=user)
        subject_entity = create_entity()
        object_entity  = create_entity()

        rtype, sym_rtype = RelationType.create(('test-subject_foobar', 'is loving'),
                                               ('test-object_foobar',  'is loved by'),
                                               is_internal=True
                                              )
        self.assertTrue(rtype.is_internal)
        self.assertTrue(sym_rtype.is_internal)
        self.assertRaises(Http404, rtype.is_not_internal_or_die)

        relation = Relation.objects.create(user=user, type=rtype,
                                           subject_entity=subject_entity,
                                           object_entity=object_entity,
                                          )
        self.assertEqual(404, self._delete(relation).status_code)
        self.get_object_or_fail(Relation, pk=relation.pk)

    def _delete_similar(self, subject, rtype, obj):
        return self.client.post('/creme_core/relation/delete/similar',
                                data={'subject_id': subject.id,
                                      'type':       rtype.id,
                                      'object_id':  obj.id,
                                     }
                               )

    def test_delete_similar01(self):
        user = self.login()

        create_entity = partial(CremeEntity.objects.create, user=user)
        subject_entity01 = create_entity()
        object_entity01  = create_entity()

        subject_entity02 = create_entity()
        object_entity02  = create_entity()

        create_rt = RelationType.create
        rtype01 = create_rt(('test-subject_love', 'is loving'), ('test-object_love', 'is loved by'))[0]
        rtype02 = create_rt(('test-subject_son',  'is son of'), ('test-object_son',  'is parent of'))[0]

        create_rel = partial(Relation.objects.create, user=user, type=rtype01, 
                             subject_entity=subject_entity01, object_entity=object_entity01
                            )

        #will be deleted (normally)
        relation01 = create_rel()
        relation02 = create_rel()

        #won't be deleted (normally)
        relation03 = create_rel(object_entity=object_entity02)
        relation04 = create_rel(subject_entity=subject_entity02)
        relation05 = create_rel(type=rtype02)

        self.assertEqual(10, Relation.objects.count())

        self.assertEqual(302, self._delete_similar(subject_entity01, rtype01, object_entity01).status_code)
        self.assertEqual(0,   Relation.objects.filter(pk__in=[relation01.pk, relation02.pk]).count())
        self.assertEqual(3,   Relation.objects.filter(pk__in=[relation03.pk, relation04.pk, relation05.pk]).count())

    def test_delete_similar02(self):
        user = self.login(is_superuser=False)
        self._set_all_creds_except_one(excluded=EntityCredentials.UNLINK)

        allowed   = CremeEntity.objects.create(user=user)
        forbidden = CremeEntity.objects.create(user=self.other_user)

        rtype = RelationType.create(('test-subject_love', 'is loving'), ('test-object_love', 'is loved by'))[0]
        create_rel = partial(Relation.objects.create, user=user, type=rtype)
        create_rel(subject_entity=allowed,   object_entity=forbidden)
        create_rel(subject_entity=forbidden, object_entity=allowed)
        self.assertEqual(4, Relation.objects.count())

        self.assertEqual(403, self._delete_similar(allowed, rtype, forbidden).status_code)
        self.assertEqual(4,   Relation.objects.count())

        self.assertEqual(403, self._delete_similar(forbidden, rtype, allowed).status_code)
        self.assertEqual(4,   Relation.objects.count())

    def test_delete_similar03(self):
        "Is internal"
        user = self.login()

        create_entity = partial(CremeEntity.objects.create, user=user)
        subject_entity = create_entity()
        object_entity  = create_entity()

        rtype = RelationType.create(('test-subject_love', 'is loving'),
                                    ('test-object_love', 'is loved by'),
                                    is_internal=True
                                   )[0]
        relation = Relation.objects.create(user=user, type=rtype,
                                           subject_entity=subject_entity,
                                           object_entity=object_entity
                                          )

        self.assertEqual(404, self._delete_similar(subject_entity, rtype, object_entity).status_code)
        self.assertEqual(1,   Relation.objects.filter(pk=relation.pk).count())

    def _aux_test_delete_all(self):
        self.assertEqual(0, Relation.objects.count())
        create_entity = CremeEntity.objects.create
        subject  = self.subject = create_entity(user=self.user)
        object01 = create_entity(user=self.user)
        object02 = create_entity(user=self.other_user)

        create_rtype = lambda *args, **kwargs: RelationType.create(*args, **kwargs)[0]
        rtypes = [create_rtype(('test-subject_foobar1', 'is loving'),
                               ('test-object_foobar1',  'is loved by')
                              ),
                  create_rtype(('test-subject_foobar2', 'is loving'),
                               ('test-object_foobar2',  'is loved by')
                              ),
                  create_rtype(('test-subject_foobar3', 'is loving'),
                               ('test-object_foobar3',  'is loved by'),
                               is_internal=True
                              ),
                 ]
        create_rel = partial(Relation.objects.create, subject_entity=subject)

        for rtype in rtypes:
            create_rel(type=rtype, object_entity=object01, user=self.user)
            create_rel(type=rtype, object_entity=object02, user=self.other_user)

    def test_delete_all01(self):
        self.login()
        self._aux_test_delete_all()
        self.assertEqual(12, Relation.objects.count())

        url = self.DELETE_ALL_URL
        self.assertPOST404(url)

        self.assertPOST200(url, data={'subject_id': self.subject.id})
        self.assertEqual(4, Relation.objects.count())
        self.assertFalse(Relation.objects.filter(type__is_internal=False))

    def test_delete_all02(self):
        self.login(is_superuser=False)
        self._set_all_creds_except_one(excluded=EntityCredentials.UNLINK)
        self._aux_test_delete_all()

        self.assertPOST403(self.DELETE_ALL_URL, data={'subject_id': self.subject.id})
        self.assertEqual(4 + 4, Relation.objects.count())#4 internals and 4 the user can't unlink because there are not his

    def test_not_copiable_relations01(self):
        user = self.login()

        self.assertEqual(0, Relation.objects.count())
        rtype1, rtype2 = RelationType.create(('test-subject_foobar', 'is loving'),
                                             ('test-object_foobar',  'is loved by'),
                                             is_copiable=False)
        rtype3, rtype4 = RelationType.create(('test-subject_foobar_copiable', 'is loving'),
                                             ('test-object_foobar_copiable',  'is loved by'),
                                             )

        create_entity = CremeEntity.objects.create
        entity1 = create_entity(user=user)
        entity2 = create_entity(user=user)

        Relation.objects.create(user=user, type=rtype1,
                                subject_entity=entity1, object_entity=entity2,
                               )
        self.assert_relation_count(((rtype1, 1), (rtype2, 1)))

        Relation.objects.create(user=user, type=rtype3,
                                subject_entity=entity1, object_entity=entity2,
                               )
        self.assert_relation_count(((rtype3, 1), (rtype4, 1)))

        entity1.clone()
        self.assert_relation_count(((rtype1, 1), (rtype2, 1), (rtype3, 2), (rtype4, 2)))

    def test_not_copiable_relations02(self):
        user = self.login()
        self.assertEqual(0, Relation.objects.count())
        rtype1, rtype2 = RelationType.create(('test-subject_foobar_copiable', 'is loving', (Contact, Organisation)),
                                             ('test-object_foobar_copiable',  'is loved by', (Contact,)))
        rtype3, rtype4 = RelationType.create(('test-subject_foobar', 'is loving', (Contact,)),
                                             ('test-object_foobar',  'is loved by', (Organisation,)),
                                             )

        contact1 = Contact.objects.create(user=user, last_name="Toto")
        contact2 = Contact.objects.create(user=user, last_name="Titi")
        orga = Organisation.objects.create(user=user, name="Toto CORP")

        #Contact1 <------> Orga
        Relation.objects.create(user=user, type=rtype1,
                                subject_entity=contact1,
                                object_entity=orga)
        Relation.objects.create(user=user, type=rtype3,
                                subject_entity=contact1,
                                object_entity=orga)

        self.assert_relation_count(((rtype1, 1), (rtype2, 1), (rtype3, 1), (rtype4, 1)))

        #Contact2 < ---- > Orga
        contact2._copy_relations(contact1)
        self.assert_relation_count(((rtype1, 2), (rtype2, 2), (rtype3, 2), (rtype4, 2)))

        orga._copy_relations(contact1)
        self.assert_relation_count(((rtype1, 3), (rtype2, 3), (rtype3, 2), (rtype4, 2)))

#    @skipIfNotInstalled('creme.tickets')
    def test_json_entity_rtypes01(self):
#        from creme.tickets.models import Ticket
        user = self.login()

        rei = Contact.objects.create(user=user, first_name='Rei', last_name='Ayanami')

        create_rtype = RelationType.create
        rtype1, rtype2 = create_rtype(('test-subject_JSP01_1', 'Predicate#1'),
                                      ('test-object_JSP01_2',  'Predicate#2'),
                                      is_internal=True
                                     )
        rtype3, rtype4 = create_rtype(('test-subject__JSP01_3', 'Predicate#3', [Contact, Organisation]),
#                                      ('test-object__JSP01_4',  'Predicate#4', [Ticket]),
                                      ('test-object__JSP01_4',  'Predicate#4', [FakeActivity]),
                                     )
        rtype5, rtype6 = create_rtype(('test-subject__JSP01_5', 'Predicate#5'),
                                      ('test-object__JSP01_6',  'Predicate#6', [Contact]),
                                     )

        url = self._build_predicates_json_url(rei)
        self.assertGET(400, url)
        self.assertGET(400, url, data={'wedontcare': 'unknown'})
        self.assertGET403(url, data={'fields': ['unknown']})

        response = self.assertGET200(url, data={'fields': ['id']})
        json_data = load_json(response.content)
        self.assertIsInstance(json_data, list)
        self.assertIn([rtype3.id], json_data)
        self.assertIn([rtype5.id], json_data)
        self.assertIn([rtype6.id], json_data)
        self.assertNotIn([rtype1.id], json_data) #internal
        self.assertNotIn([rtype4.id], json_data) #CT constraint

        nerv = Organisation.objects.create(user=user, name='Nerv')
        response = self.assertGET200(self._build_predicates_json_url(nerv),
                                     data={'fields': ['id', 'unicode']}
                                    )
        self.assertIn([rtype3.id, unicode(rtype3)],
                      load_json(response.content)
                     )

    def test_json_entity_rtypes02(self):
#        user = self.login(is_superuser=False)
        user = self.login(is_superuser=False, allowed_apps=['documents'])
        rei = Contact.objects.create(user=user, first_name='Rei', last_name='Ayanami')
        self.assertGET403(self._build_predicates_json_url(rei),
                          data={'fields': ['id']}
                         )
