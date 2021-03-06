# -*- coding: utf-8 -*-

try:
    from functools import partial

    from django.contrib.auth import get_user_model
    from django.contrib.contenttypes.models import ContentType
    from django.test import override_settings
    from django.urls import reverse
    from django.utils.translation import gettext as _

    from creme.creme_core.tests.fake_constants import FAKE_REL_SUB_EMPLOYED_BY
    from creme.creme_core.tests.views.base import ViewsTestCase

    from creme.creme_core.core.entity_cell import (
        EntityCellRegularField,
        EntityCellCustomField,
        EntityCellFunctionField,
        EntityCellRelation,
    )
    from creme.creme_core.core.entity_filter.operators import EQUALS
    from creme.creme_core.core.entity_filter.condition_handler import RegularFieldConditionHandler
    from creme.creme_core.core.function_field import function_field_registry
    from creme.creme_core.models import (
        HeaderFilter, FieldsConfig,
        RelationType, CustomField,
        EntityFilter,   # EntityFilterCondition
        FakeContact, FakeOrganisation, FakeProduct, FakeMailingList,
    )
except Exception as e:
    print('Error in <{}>: {}'.format(__name__, e))


class HeaderFilterViewsTestCase(ViewsTestCase):
    DELETE_URL = reverse('creme_core__delete_hfilter')

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.contact_ct = ContentType.objects.get_for_model(FakeContact)

    def assertCellsEqual(self, cells1, cells2):
        self.assertEqual(len(cells1), len(cells2))

        for cell1, cell2 in zip(cells1, cells2):
            self.assertIs(cell1.__class__, cell2.__class__)
            self.assertEqual(cell1.value, cell2.value)

    def _build_add_url(self, ctype):
        return reverse('creme_core__create_hfilter', args=(ctype.id,))

    def _build_get4ctype_url(self, ctype):
        return '{}?ct_id={}'.format(reverse('creme_core__hfilters'), ctype.id)

    @override_settings(FILTERS_INITIAL_PRIVATE=False)
    def test_create01(self):
        self.login()

        ct = ContentType.objects.get_for_model(FakeMailingList)
        self.assertFalse(HeaderFilter.objects.filter(entity_type=ct))

        url = self._build_add_url(ct)
        response = self.assertGET200(url)
        self.assertTemplateUsed(response, 'creme_core/forms/header-filter.html')
        self.assertIn(_('Create a view of list for «%(ctype)s»') % {'ctype': 'Test Mailing list'},
                      response.content.decode(),
                     )
        self.assertIs(response.context['form'].initial.get('is_private'), False)

        name = 'DefaultHeaderFilter'
        response = self.client.post(url, data={'name':  name,
                                               'cells': 'regular_field-created',
                                              }
                                   )
        self.assertNoFormError(response, status=302)

        hfilters = HeaderFilter.objects.filter(entity_type=ct)
        self.assertEqual(1, len(hfilters))

        hfilter = hfilters[0]
        self.assertEqual(name, hfilter.name)
        self.assertIsNone(hfilter.user)
        self.assertTrue(hfilter.is_custom)
        self.assertFalse(hfilter.is_private)

        cells = hfilter.cells
        self.assertEqual(1, len(cells))

        cell = cells[0]
        self.assertIsInstance(cell, EntityCellRegularField)
        self.assertEqual('created', cell.value)
        # self.assertEqual('created__range', cell.filter_string)
        self.assertIs(cell.is_hidden, False)

        lv_url = FakeMailingList.get_lv_absolute_url()
        self.assertRedirects(response, lv_url)

        # --
        context = self.assertGET200(lv_url).context
        selected_hfilter = context['header_filters'].selected
        self.assertIsInstance(selected_hfilter, HeaderFilter)
        self.assertEqual(hfilter.id, selected_hfilter.id)
        self.assertEqual(hfilter.id, context['list_view_state'].header_filter_id)

    def test_create02(self):
        user = self.login()

        lv_url = FakeContact.get_lv_absolute_url()

        # Create a view to post the entity filter
        HeaderFilter.create(
            pk='creme_core-tests_views_header_filter_test_create02',
            name='A FakeContact view',  # Starts with "A" => first
            model=FakeContact,
            cells_desc=[(EntityCellRegularField, {'name': 'last_name'}),
                        (EntityCellRegularField, {'name': 'first_name'}),
                        (EntityCellRegularField, {'name': 'email'}),
                      ],
        )

        # Set a filter in the session (should be kept)
        efilter = EntityFilter.create(
            'creme_core-tests_views_header_filter_test_create02',
            name='Misato', model=FakeContact,
            is_custom=True,
            conditions=[
                # EntityFilterCondition.build_4_field(
                #     model=FakeContact,
                #     operator=EntityFilterCondition.EQUALS,
                #     name='first_name', values=['Misato'],
                # ),
                RegularFieldConditionHandler.build_condition(
                    model=FakeContact, field_name='first_name',
                    operator=EQUALS, values=['Misato'],
                ),
            ],
        )
        response = self.assertPOST200(lv_url, data={'filter': efilter.id})
        self.assertEqual(efilter.id, response.context['list_view_state'].entity_filter_id)

        # --
        ct = self.contact_ct
        loves = RelationType.create(('test-subject_love', 'Is loving'),
                                    ('test-object_love',  'Is loved by')
                                   )[0]
        customfield = CustomField.objects.create(name='Size (cm)',
                                                 field_type=CustomField.INT,
                                                 content_type=ct,
                                                )
        # funcfield = FakeContact.function_fields.get('get_pretty_properties')
        funcfield = function_field_registry.get(FakeContact, 'get_pretty_properties')

        url = self._build_add_url(ct)
        response = self.assertGET200(url)

        with self.assertNoException():
            cells_f = response.context['form'].fields['cells']

        build_4_field = partial(EntityCellRegularField.build, model=FakeContact)
        self.assertCellsEqual([build_4_field(name='first_name'),
                               build_4_field(name='last_name'),
                               EntityCellRelation(model=FakeContact,
                                                  rtype=RelationType.objects.get(pk=FAKE_REL_SUB_EMPLOYED_BY),
                                                 ),
                              ],
                              cells_f.initial
                             )

        field_name = 'first_name'
        name = 'DefaultHeaderFilter'
        response = self.client.post(url, follow=True,
                                    data={'name': name,
                                          'user': user.id,
                                          'is_private': 'on',
                                          'cells': 'relation-{rtype},'
                                                   'regular_field-{rfield},'
                                                   'function_field-{ffield},'
                                                   'custom_field-{cfield}'.format(
                                                        rfield=field_name,
                                                        cfield=customfield.id,
                                                        rtype=loves.id,
                                                        ffield=funcfield.name,
                                                    )
                                         }
                                   )
        self.assertNoFormError(response)

        hfilter = self.get_object_or_fail(HeaderFilter, name=name)
        self.assertEqual(user, hfilter.user)
        self.assertTrue(hfilter.is_private)

        cells = hfilter.cells
        self.assertEqual(4, len(cells))

        cell = cells[0]
        self.assertIsInstance(cell, EntityCellRelation)
        self.assertEqual(loves.id, cell.value)

        cell = cells[1]
        self.assertIsInstance(cell, EntityCellRegularField)
        self.assertEqual(field_name, cell.value)

        cell = cells[2]
        self.assertIsInstance(cell, EntityCellFunctionField)
        self.assertEqual(funcfield.name, cell.value)

        cell = cells[3]
        self.assertIsInstance(cell, EntityCellCustomField)
        self.assertEqual(str(customfield.id), cell.value)

        self.assertRedirects(response, lv_url)

        # --
        context = self.assertGET200(lv_url).context
        selected_hfilter = context['header_filters'].selected
        self.assertIsInstance(selected_hfilter, HeaderFilter)
        self.assertEqual(hfilter.id, selected_hfilter.id)

        lvs = context['list_view_state']
        self.assertEqual(hfilter.id, lvs.header_filter_id)
        self.assertEqual(efilter.id, lvs.entity_filter_id)

    def test_create03(self):
        "Check app credentials"
        self.login(is_superuser=False, allowed_apps=['documents'])

        uri = self._build_add_url(self.contact_ct)
        self.assertGET403(uri)

        self.role.allowed_apps = ['documents', 'creme_core']
        self.role.save()

        self.assertGET200(uri)

    def test_create04(self):
        "Cannot create a private filter for another user (but OK with one of our teams)"
        user = self.login()

        User = get_user_model()
        my_team = User.objects.create(username='TeamTitan', is_team=True)
        my_team.teammates = [user, self.other_user]

        a_team = User.objects.create(username='A-team', is_team=True)
        a_team.teammates = [self.other_user]

        name = 'DefaultHeaderFilter'

        def post(owner):
            return self.assertPOST200(self._build_add_url(self.contact_ct), follow=True,
                                      data={'name': name,
                                            'user': owner.id,
                                            'is_private': 'on',
                                            'cells': 'regular_field-first_name',
                                           },
                                     )

        response = post(self.other_user)
        msg = _('A private view of list must belong to you (or one of your teams).')
        self.assertFormError(response, 'form', 'user', msg)

        response = post(a_team)
        self.assertFormError(response, 'form', 'user', msg)

        response = post(my_team)
        self.assertNoFormError(response)
        self.get_object_or_fail(HeaderFilter, name=name)

    def test_create05(self):
        "Use cancel_url for redirection."
        self.login()

        callback = FakeOrganisation.get_lv_absolute_url()
        response = self.client.post(self._build_add_url(self.contact_ct), follow=True,
                                    data={'name':      'DefaultHeaderFilter',
                                          'cells':     'regular_field-first_name',
                                          'cancel_url': callback,
                                         },
                                   )

        self.assertNoFormError(response)
        self.assertRedirects(response, callback)

    def test_create06(self):
        "A staff user can create a private filter for another user"
        self.login(is_staff=True)

        name = 'DefaultHeaderFilter'
        response = self.client.post(self._build_add_url(self.contact_ct), follow=True,
                                    data={'name': name,
                                          'user': self.other_user.id,
                                          'is_private': 'on',
                                          'cells': 'regular_field-first_name',
                                         },
                                   )

        self.assertNoFormError(response)
        self.get_object_or_fail(HeaderFilter, name=name)

    def test_create07(self):
        "Not an Entity type"
        self.login()
        self.assertGET409(self._build_add_url(ContentType.objects.get_for_model(RelationType)))

    def test_create08(self):
        "FieldsConfig"
        self.login()

        valid_fname = 'last_name'
        hidden_fname = 'phone'
        FieldsConfig.create(FakeContact, descriptions=[(hidden_fname, {FieldsConfig.HIDDEN: True})])

        response = self.assertGET200(self._build_add_url(self.contact_ct))

        with self.assertNoException():
            widget = response.context['form'].fields['cells'].widget
            choices_keys = {c[0] for c in widget.model_fields}

        rf_prefix = 'regular_field-'
        self.assertIn(rf_prefix + valid_fname,     choices_keys)
        self.assertNotIn(rf_prefix + hidden_fname, choices_keys)

    @override_settings(FILTERS_INITIAL_PRIVATE=True)
    def test_create09(self):
        "Use FILTERS_INITIAL_PRIVATE"
        self.login()

        response = self.assertGET200(self._build_add_url(self.contact_ct))
        self.assertIs(response.context['form'].initial.get('is_private'), True)

    def test_create_missing_lv_absolute_url(self):
        "Missing get_lv_absolute_url() classmethod"
        with self.assertRaises(AttributeError):
            FakeProduct.get_lv_absolute_url()

        self.login()

        ct = ContentType.objects.get_for_model(FakeProduct)
        self.assertFalse(HeaderFilter.objects.filter(entity_type=ct))

        url = self._build_add_url(ct)
        self.assertGET200(url)

        name = 'DefaultHeaderFilter'
        response = self.client.post(url, data={'name':  name,
                                               'cells': 'regular_field-name',
                                              }
                                   )

        self.assertNoFormError(response, status=302)
        self.assertRedirects(response, '/')

    def test_edit01(self):
        self.login()

        field1 = 'first_name'
        hf = HeaderFilter.create(pk='tests-hf_contact', name='Contact view',
                                 model=FakeContact, is_custom=True,
                                 cells_desc=[EntityCellRegularField.build(model=FakeContact, name=field1)],
                                )

        url = hf.get_edit_absolute_url()
        response = self.assertGET200(url)
        self.assertTemplateUsed(response, 'creme_core/forms/header-filter.html')
        self.assertIn(_('Edit the view of list «%(view)s»') % {'view': hf.name},
                      response.content.decode()
                     )

        with self.assertNoException():
            context = response.context
            cells_f      = context['form'].fields['cells']
            submit_label = context['submit_label']

        self.assertCellsEqual(hf.cells, cells_f.initial)
        self.assertEqual(_('Save the modified view'), submit_label)

        name = 'Entity view v2'
        field2 = 'last_name'
        response = self.client.post(url, data={'name':  name,
                                               'cells': 'regular_field-{},'
                                                        'regular_field-{}'.format(
                                                                field1, field2,
                                                            ),
                                              },
                                   )
        self.assertNoFormError(response, status=302)

        hf = self.refresh(hf)
        self.assertEqual(name, hf.name)
        self.assertTrue(hf.is_custom)

        cells = hf.cells
        self.assertEqual(2,      len(cells))
        self.assertEqual(field1, cells[0].value)
        self.assertEqual(field2, cells[1].value)

        self.assertRedirects(response, FakeContact.get_lv_absolute_url())

    def test_edit02(self):
        "Not custom -> can be still edited"
        self.login()

        name = 'Contact view'
        field1 = 'first_name'
        hf = HeaderFilter.create(pk='tests-hf_contact', name=name,
                                 model=FakeContact, is_custom=False,
                                 cells_desc=[EntityCellRegularField.build(model=FakeContact, name=field1)],
                                )

        url = hf.get_edit_absolute_url()
        self.assertGET200(url)

        name += ' (edited)'
        field2 = 'last_name'
        response = self.client.post(url, data={'name':  name,
                                               'cells': 'regular_field-%s,'
                                                        'regular_field-%s' % (
                                                                field2, field1,
                                                            ),
                                              },
                                   )
        self.assertNoFormError(response, status=302)

        hf = self.refresh(hf)
        self.assertEqual(name, hf.name)
        self.assertFalse(hf.is_custom)

        cells = hf.cells
        self.assertEqual(2,      len(cells))
        self.assertEqual(field2, cells[0].value)
        self.assertEqual(field1, cells[1].value)

    def test_edit03(self):
        "Cannot edit HeaderFilter that belongs to another user"
        self.login(is_superuser=False)

        hf = HeaderFilter.create(pk='tests-hf_contact', name='Contact view',
                                 model=FakeContact, is_custom=True, user=self.other_user,
                                )
        self.assertGET403(hf.get_edit_absolute_url())

    def test_edit04(self):
        "User do not have the app credentials"
        user = self.login(is_superuser=False, allowed_apps=['documents'])

        hf = HeaderFilter.create(pk='tests-hf_contact', name='Contact view',
                                 model=FakeContact, is_custom=True, user=user,
                                )
        self.assertGET403(hf.get_edit_absolute_url())

    def test_edit05(self):
        "User belongs to the team -> OK"
        user = self.login(is_superuser=False)

        my_team = get_user_model().objects.create(username='TeamTitan', is_team=True)
        my_team.teammates = [user]

        hf = HeaderFilter.create(pk='tests-hf_contact', name='Contact view',
                                 model=FakeContact, is_custom=True, user=my_team,
                                )
        self.assertGET200(hf.get_edit_absolute_url())

    def test_edit06(self):
        "User does not belong to the team -> error"
        self.login(is_superuser=False)

        User = get_user_model()
        my_team = User.objects.create(username='TeamTitan', is_team=True)
        # my_team.teammates = [self.user] # <=====

        a_team = User.objects.create(username='A-team', is_team=True)
        a_team.teammates = [self.user]

        hf = HeaderFilter.create(pk='tests-hf_contact', name='Contact view',
                                 model=FakeContact, is_custom=True, user=my_team,
                                )
        self.assertGET403(hf.get_edit_absolute_url())

    def test_edit07(self):
        "Private filter -> cannot be edited by another user (even a super-user)"
        self.login()

        hf = HeaderFilter.create(pk='tests-hf_contact', name='Contact view',
                                 model=FakeContact, is_custom=True,
                                 is_private=True, user=self.other_user,
                                )
        self.assertGET403(hf.get_edit_absolute_url())

    def test_edit08(self):
        "Staff users can edit all HeaderFilters + private filters must be assigned"
        self.login(is_staff=True)

        hf = HeaderFilter.create(pk='tests-hf_contact', name='Contact view',
                                 model=FakeContact, is_custom=True,
                                 is_private=True, user=self.other_user,
                                )
        url = hf.get_edit_absolute_url()
        self.assertGET200(url)

        response = self.assertPOST200(url, follow=True,
                                      data={'name':       hf.name,
                                            'user':       '',
                                            'is_private': 'on',
                                            'cells':      'regular_field-last_name',
                                           }
                                     )
        self.assertFormError(response, 'form', 'user',
                             _('A private view of list must be assigned to a user/team.')
                            )

    def test_edit09(self):
        "Not custom filter cannot be private + callback URL."
        self.login()

        hf = HeaderFilter.create(pk='tests-hf_contact', name='Contact view',
                                 model=FakeContact, is_custom=False,
                                )
        url = hf.get_edit_absolute_url()
        self.assertGET200(url)

        callback = FakeOrganisation.get_lv_absolute_url()
        response = self.client.post(url, data={'name':       hf.name,
                                               'user':       self.user.id,
                                               'is_private': 'on',  # Should not be used
                                               'cells':      'regular_field-last_name',
                                               'cancel_url': callback,
                                              }
                                   )
        self.assertNoFormError(response, status=302)
        self.assertFalse(self.refresh(hf).is_private)

        self.assertRedirects(response, callback)

    def test_edit10(self):
        "FieldsConfig."
        self.login()

        valid_fname = 'last_name'
        hidden_fname1 = 'phone'
        hidden_fname2 = 'birthday'
        build_cell = partial(EntityCellRegularField.build, model=FakeContact)
        hf = HeaderFilter.create(pk='tests-hf_contact', name='Contact view',
                                 model=FakeContact, is_custom=True,
                                 cells_desc=[build_cell(name=valid_fname),
                                             build_cell(name=hidden_fname1),
                                            ],
                                )
        FieldsConfig.create(FakeContact,
                            descriptions=[(hidden_fname1, {FieldsConfig.HIDDEN: True}),
                                          (hidden_fname2, {FieldsConfig.HIDDEN: True}),
                                         ]
                           )

        response = self.assertGET200(hf.get_edit_absolute_url())

        with self.assertNoException():
            widget = response.context['form'].fields['cells'].widget
            choices_keys = {c[0] for c in widget.model_fields}

        rf_prefix = 'regular_field-'
        self.assertIn(rf_prefix + valid_fname,   choices_keys)
        self.assertIn(rf_prefix + hidden_fname1, choices_keys)  # Was already in the HeaderFilter => still proposed
        self.assertNotIn(rf_prefix + hidden_fname2, choices_keys)

    def test_delete01(self):
        self.login()

        hf = HeaderFilter.create(pk='tests-hf_contact', name='Contact view',
                                 model=FakeContact, is_custom=True,
                                 cells_desc=[EntityCellRegularField.build(model=FakeContact, name='first_name')],
                                )
        self.assertPOST200(self.DELETE_URL, follow=True, data={'id': hf.id})
        self.assertDoesNotExist(hf)

    def test_delete02(self):
        "Not custom -> not deletable."
        self.login()

        hf = HeaderFilter.create(pk='tests-hf_contact', name='Contact view',
                                 model=FakeContact, is_custom=False,
                                )
        self.client.post(self.DELETE_URL, data={'id': hf.id})
        self.assertStillExists(hf)

    def test_delete03(self):
        "Belongs to another user."
        self.login(is_superuser=False)

        hf = HeaderFilter.create(pk='tests-hf_contact', name='Contact view',
                                 model=FakeContact, is_custom=True, user=self.other_user,
                                )
        self.client.post(self.DELETE_URL, data={'id': hf.id})
        self.assertStillExists(hf)

    def test_delete04(self):
        "The user belongs to the owner team -> OK."
        user = self.login(is_superuser=False)

        my_team = get_user_model().objects.create(username='TeamTitan', is_team=True)
        my_team.teammates = [user]

        hf = HeaderFilter.create(pk='tests-hf_contact', name='Contact view',
                                 model=FakeContact, is_custom=True, user=my_team,
                                )
        self.assertPOST200(self.DELETE_URL, data={'id': hf.id}, follow=True)
        self.assertDoesNotExist(hf)

    def test_delete05(self):
        "Belongs to a team (not mine) -> KO."
        user = self.login(is_superuser=False)

        User = get_user_model()
        a_team = User.objects.create(username='TeamTitan', is_team=True)
        a_team.teammates = [self.other_user]

        my_team = User.objects.create(username='A-team', is_team=True)
        my_team.teammates = [user]

        hf = HeaderFilter.create(pk='tests-hf_contact', name='Contact view',
                                 model=FakeContact, is_custom=True, user=a_team,
                                )
        self.client.post(self.DELETE_URL, data={'id': hf.id}, follow=True)
        self.assertStillExists(hf)

    def test_delete06(self):
        "Logged as super user."
        self.login()

        hf = HeaderFilter.create(pk='tests-hf_contact', name='Contact view',
                                 model=FakeContact, is_custom=True, user=self.other_user,
                                )
        self.client.post(self.DELETE_URL, data={'id': hf.id})
        self.assertDoesNotExist(hf)

    def test_hfilters_for_ctype01(self):
        self.login()

        response = self.assertGET200(self._build_get4ctype_url(ContentType.objects.get_for_model(FakeMailingList)))
        self.assertEqual([], response.json())

    def test_hfilters_for_ctype02(self):
        user = self.login()

        create_hf = HeaderFilter.create
        name01 = 'ML view01'
        name02 = 'ML view02'
        name03 = 'ML view03'
        pk_fmt = 'tests-hf_ml{}'.format
        hf01 = create_hf(pk=pk_fmt(1),  name=name01,      model=FakeMailingList,  is_custom=False)
        hf02 = create_hf(pk=pk_fmt(2),  name=name02,      model=FakeMailingList,  is_custom=True)
        create_hf(pk='tests-hf_orga01', name='Orga view', model=FakeOrganisation, is_custom=True)
        hf03 = create_hf(pk=pk_fmt(3),  name=name03,      model=FakeMailingList,  is_custom=True, is_private=True, user=user)
        create_hf(pk=pk_fmt(4),         name='Private',   model=FakeMailingList,  is_custom=True, is_private=True, user=self.other_user)

        expected = [[hf01.id, name01], [hf02.id, name02], [hf03.id, name03]]
        ct = ContentType.objects.get_for_model(FakeMailingList)
        response = self.assertGET200(self._build_get4ctype_url(ct))
        self.assertEqual(expected, response.json())

    def test_hfilters_for_ctype03(self):
        "No app credentials"
        self.login(is_superuser=False, allowed_apps=['documents'])
        self.assertGET403(self._build_get4ctype_url(self.contact_ct))
