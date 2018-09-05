# -*- coding: utf-8 -*-

try:
    from django.contrib.sessions.models import Session
    from django.urls import reverse
    from django.utils.html import escape
    from django.utils.translation import ugettext as _

    from .base import ViewsTestCase, BrickTestCaseMixin
    from .. import fake_forms

    from creme.creme_core.bricks import PropertiesBrick
    from creme.creme_core.gui.last_viewed import LastViewedItem
    from creme.creme_core.models import FakeOrganisation, FakeContact, Imprint
except Exception as e:
    print('Error in <{}>: {}'.format(__name__, e))


class DetailTestCase(ViewsTestCase, BrickTestCaseMixin):
    # TODO: factorise with tests.gui.test_misc.GuiTestCase
    class FakeRequest:
        def __init__(self, user):
            user_id = str(user.id)
            sessions = [d for d in (s.get_decoded() for s in Session.objects.all())
                            if d.get('_auth_user_id') == user_id
                       ]
            assert 1 == len(sessions)
            self.session = sessions[0]

    def test_detail_legacy01(self):
        user = self.login()
        self.assertFalse(LastViewedItem.get_all(self.FakeRequest(user)))
        self.assertFalse(Imprint.objects.all())

        hq = FakeOrganisation.objects.create(user=user, name='HQ')
        response = self.assertGET200(hq.get_absolute_url())
        self.assertTemplateUsed(response, 'creme_core/generics/view_entity.html')

        # -----
        last_items = LastViewedItem.get_all(self.FakeRequest(user))
        self.assertEqual(1, len(last_items))
        self.assertEqual(hq.id, last_items[0].pk)

        # -----
        imprints = Imprint.objects.all()
        self.assertEqual(1, len(imprints))
        self.assertEqual(imprints[0].entity.get_real_entity(), hq)

        # -----
        self.get_brick_node(self.get_html_tree(response.content), PropertiesBrick.id_)

    def test_detail_legacy02(self):
        "Object does not exist"
        self.login()

        response = self.assertGET404(reverse('creme_core__view_fake_image', args=(1024,)))
        self.assertTemplateUsed(response, '404.html')

    def test_detail_legacy03(self):
        "Not allowed"
        self.login(is_superuser=False)
        hq = FakeOrganisation.objects.create(user=self.other_user, name='HQ')

        response = self.assertGET403(hq.get_absolute_url())
        self.assertTemplateUsed(response, 'creme_core/forbidden.html')

    def test_detail_legacy04(self):
        "Not logged"
        user = self.login()
        hq = FakeOrganisation.objects.create(user=user, name='HQ')

        self.client.logout()
        url = hq.get_absolute_url()
        response = self.assertGET(302, url)
        self.assertRedirects(response, '{}?next={}'.format(reverse('creme_login'), url))

    def test_detail01(self):
        user = self.login()
        self.assertFalse(LastViewedItem.get_all(self.FakeRequest(user)))
        self.assertFalse(Imprint.objects.all())

        fox = FakeContact.objects.create(user=user, first_name='Fox', last_name='McCloud')
        url = fox.get_absolute_url()
        self.assertPOST(405, url)  # TODO: specific template for 405 errors ?

        response = self.assertGET200(url)
        self.assertTemplateUsed(response, 'creme_core/generics/view_entity.html')

        # -----
        last_items = LastViewedItem.get_all(self.FakeRequest(user))
        self.assertEqual(1, len(last_items))
        self.assertEqual(fox.id, last_items[0].pk)

        # -----
        imprints = Imprint.objects.all()
        self.assertEqual(1, len(imprints))
        self.assertEqual(imprints[0].entity.get_real_entity(), fox)

        # -----
        self.get_brick_node(self.get_html_tree(response.content), PropertiesBrick.id_)

    def test_detail02(self):
        "Object does not exist"
        self.login()

        response = self.assertGET404(reverse('creme_core__view_fake_contact', args=(1024,)))
        self.assertTemplateUsed(response, '404.html')

    def test_detail03(self):
        "Not super-user"
        user = self.login(is_superuser=False)
        fox = FakeContact.objects.create(user=user, first_name='Fox', last_name='McCloud')
        self.assertGET200(fox.get_absolute_url())

    def test_detail04(self):
        "Not logged"
        user = self.login()
        fox = FakeContact.objects.create(user=user, first_name='Fox', last_name='McCloud')
        url = fox.get_absolute_url()

        self.client.logout()
        response = self.assertGET(302, url)
        self.assertRedirects(response, '{}?next={}'.format(reverse('creme_login'), url))

    def test_detail05(self):
        "Viewing is not allowed (model credentials)"
        self.login(is_superuser=False)
        fox = FakeContact.objects.create(user=self.other_user, first_name='Fox', last_name='McCloud')

        response = self.assertGET403(fox.get_absolute_url())
        self.assertTemplateUsed(response, 'creme_core/forbidden.html')
        self.assertIn(escape(_('You are not allowed to view this entity: {}').format(
                                _('Entity #{id} (not viewable)').format(id=fox.id)
                            )),
                      response.content.decode()
                     )

    def test_detail06(self):
        "Viewing is not allowed (app credentials)"
        # NB: not need to create an instance, the "app" permission must be checked before the SQL query.
        self.login(is_superuser=False, allowed_apps=('creme_config',))  # Not "creme_core"

        response = self.assertGET403(reverse('creme_core__view_fake_contact', args=(1024,)))
        self.assertTemplateUsed(response, 'creme_core/forbidden.html')
        self.assertIn(escape(_('You are not allowed to access to the app: {}').format(_('Core'))),
                      response.content.decode()
                     )


class CreationTestCase(ViewsTestCase):
    def test_add_entity01(self):
        user = self.login()

        url = reverse('creme_core__create_fake_organisation')
        response = self.assertGET200(url)
        self.assertTemplateUsed(response, 'creme_core/generics/blockform/add.html')

        context = response.context
        self.assertIsInstance(context.get('form'), fake_forms.FakeOrganisationForm)
        self.assertEqual(_('Create an organisation'), context.get('title'))
        self.assertEqual(_('Save the organisation'),  context.get('submit_label'))
        self.assertIsNone(context.get('cancel_url', -1))

        count = FakeOrganisation.objects.count()
        name  = 'Spectre'
        description = 'DESCRIPTION'
        response = self.client.post(url, follow=True,
                                    data={'user':        user.id,
                                          'name':        name,
                                          'description': description,
                                         }
                                   )
        self.assertNoFormError(response)
        self.assertEqual(count + 1, FakeOrganisation.objects.count())

        orga = self.get_object_or_fail(FakeOrganisation, name=name)
        self.assertEqual(description, orga.description)

        self.assertRedirects(response, orga.get_absolute_url())

    def test_add_entity02(self):
        "ValidationError + cancel_url"
        user = self.login()

        url = reverse('creme_core__create_fake_organisation')
        lv_url = FakeOrganisation.get_lv_absolute_url()
        response = self.assertGET200(url, HTTP_REFERER='http://testserver' + lv_url)
        self.assertEqual(lv_url, response.context.get('cancel_url'))

        response = self.client.post(url, follow=True,
                                    data={'user': user.id,
                                          # 'name': name,  # NB: Missing
                                          'cancel_url': lv_url,
                                         }
                                   )
        self.assertFormError(response, 'form', 'name', _('This field is required.'))
        self.assertEqual(lv_url, response.context.get('cancel_url'))

    def test_add_entity03(self):
        "Not app credentials"
        self.login(is_superuser=False, allowed_apps=['creme_config'])

        response = self.assertGET403(reverse('creme_core__create_fake_organisation'))
        self.assertTemplateUsed(response, 'creme_core/forbidden.html')

    def test_add_entity04(self):
        "Not creation credentials"
        self.login(is_superuser=False, creatable_models=[FakeContact])  # Not FakeOrganisation

        response = self.assertGET403(reverse('creme_core__create_fake_organisation'))
        self.assertTemplateUsed(response, 'creme_core/forbidden.html')

    def test_add_entity05(self):
        "Not logged"
        url = reverse('creme_core__create_fake_organisation')
        response = self.assertGET(302, url)
        self.assertRedirects(response, '{}?next={}'.format(reverse('creme_login'), url))

    def test_add_entity06(self):
        "Not super-user"
        self.login(is_superuser=False, creatable_models=[FakeOrganisation])
        self.assertGET200(reverse('creme_core__create_fake_organisation'))

    def test_entity_creation01(self):
        user = self.login()

        url = reverse('creme_core__create_fake_contact')
        response = self.assertGET200(url)
        self.assertTemplateUsed(response, 'creme_core/generics/blockform/add.html')

        context = response.context
        self.assertIsInstance(context.get('form'), fake_forms.FakeContactForm)
        self.assertEqual(_('Create a contact'), context.get('title'))
        self.assertEqual(_('Save the contact'), context.get('submit_label'))

        count = FakeContact.objects.count()
        first_name = 'Spike'
        last_name  = 'Spiegel'
        response = self.client.post(url, follow=True,
                                    data={'user':       user.id,
                                          'first_name': first_name,
                                          'last_name':  last_name,
                                         }
                                   )
        self.assertNoFormError(response)
        self.assertEqual(count + 1, FakeContact.objects.count())
        contact = self.get_object_or_fail(FakeContact, first_name=first_name, last_name=last_name)
        self.assertRedirects(response, contact.get_absolute_url())

    def test_entity_creation02(self):
        "ValidationError + cancel_url"
        user = self.login()

        url = reverse('creme_core__create_fake_contact')
        lv_url = FakeContact.get_lv_absolute_url()
        response = self.assertGET200(url, HTTP_REFERER='http://testserver' + lv_url)
        self.assertEqual(lv_url, response.context.get('cancel_url'))

        response = self.client.post(url, follow=True,
                                    data={'user': user.id,
                                          # 'last_name': name,  # NB: Missing
                                          'cancel_url': lv_url,
                                          }
                                    )
        self.assertFormError(response, 'form', 'last_name', _('This field is required.'))
        self.assertEqual(lv_url, response.context.get('cancel_url'))

    def test_entity_creation03(self):
        "Not app credentials"
        self.login(is_superuser=False, allowed_apps=['creme_config'])

        response = self.assertGET403(reverse('creme_core__create_fake_contact'))
        self.assertTemplateUsed(response, 'creme_core/forbidden.html')
        self.assertIn(escape(_('You are not allowed to access to the app: {}').format(_('Core'))),
                      response.content.decode()
                     )

    def test_entity_creation04(self):
        "Not creation credentials"
        self.login(is_superuser=False, creatable_models=[FakeOrganisation])  # Not FakeContact

        response = self.assertGET403(reverse('creme_core__create_fake_contact'))
        self.assertTemplateUsed(response, 'creme_core/forbidden.html')

    def test_entity_creation05(self):
        "Not logged"
        url = reverse('creme_core__create_fake_contact')
        response = self.assertGET(302, url)
        self.assertRedirects(response, '{}?next={}'.format(reverse('creme_login'), url))

    def test_entity_creation06(self):
        "Not super-user"
        self.login(is_superuser=False, creatable_models=[FakeContact])
        self.assertGET200(reverse('creme_core__create_fake_contact'))
