# -*- coding: utf-8 -*-

try:
    from json import JSONEncoder

    from django.contrib.contenttypes.models import ContentType
    from django.utils.translation import ugettext as _

    from .base import CremeTestCase
    from ..fake_models import (FakeContact as Contact,
            FakeOrganisation as Organisation, FakeCivility as Civility)

    #from creme.persons.models import Contact, Civility, Organisation
except Exception as e:
    print('Error in <%s>: %s' % (__name__, e))


__all__ = ('QuickFormTestCase',)


class QuickFormTestCase(CremeTestCase):
    @classmethod
    def setUpClass(cls):
        CremeTestCase.setUpClass()
#        cls.populate('creme_core', 'persons')
        cls.populate('creme_core')

    def quickform_data(self, count):
        return {'form-INITIAL_FORMS':  '0',
                'form-MAX_NUM_FORMS':  '',
                'form-TOTAL_FORMS':    '%s' % count,
                'csrfmiddlewaretoken': '08b8b225c536b4fd25d16f5ed8be3839',
                'whoami':              '1335517612234535305',
               }

    def quickform_data_append(self, data, id, first_name='', last_name='', email='', organisation='', phone=''):
        return data.update({
                 'form-%d-email' % id:        email,
                 'form-%d-last_name' % id:    last_name,
                 'form-%d-first_name' % id:   first_name,
                 'form-%d-organisation' % id: organisation,
                 'form-%d-phone' % id:        phone,
                 'form-%d-user' % id:         self.user.id,
               })

    def _build_quickform_url(self, model, count=1):
        return '/creme_core/quickforms/%d/%d' % (ContentType.objects.get_for_model(model).pk, count)

    def test_add_unknown_ctype(self):
        self.login()

        invalid_id = 10000
        self.assertFalse(ContentType.objects.filter(id=invalid_id))

        url = '/creme_core/quickforms/%s/1' % invalid_id
        self.assertGET404(url)

        data = self.quickform_data(1)
        self.quickform_data_append(data, 0, last_name='Kirika')

        self.assertPOST404(url, data)

    def test_add_unregistered_ctype(self):
        self.login()
        self.assertGET404(self._build_quickform_url(Civility))

        data = self.quickform_data(1)
        self.quickform_data_append(data, 0, last_name='Kirika')

        self.assertPOST404(self._build_quickform_url(Civility), data)

    def test_add_unallowed(self):
#        self.login(is_superuser=False, allowed_apps=('creme_core', 'persons'),
        self.login(is_superuser=False,
                   creatable_models=[Organisation],
                  )

        self.assertGET403(self._build_quickform_url(Contact))
        self.assertGET200(self._build_quickform_url(Organisation))

        data = self.quickform_data(1)
        self.quickform_data_append(data, 0, last_name='Kirika')

        self.assertPOST403(self._build_quickform_url(Contact), data)
        self.assertPOST200(self._build_quickform_url(Organisation), data)

    def test_add_empty_form(self):
        self.login()
        count = Contact.objects.count()

        data = self.quickform_data(1)
        self.quickform_data_append(data, 0)

        response = self.assertPOST200(self._build_quickform_url(Contact), data)
        self.assertFormError(response, 'form', 'last_name', _('This field is required.'))
        self.assertFormSetError(response, 'formset', 0, 'last_name', [_(u'This field is required.')])

        self.assertEqual(count, Contact.objects.count())

    def test_add_multiple_empty_form(self):
        self.login()
        count = Contact.objects.count()

        data = self.quickform_data(3)
        self.quickform_data_append(data, 0)
        self.quickform_data_append(data, 1)
        self.quickform_data_append(data, 2)

        response = self.assertPOST200(self._build_quickform_url(Contact, 3), data)
        self.assertFormSetError(response, 'formset', 0, 'last_name', [_(u'This field is required.')])
        self.assertFormSetError(response, 'formset', 1, 'last_name', [_(u'This field is required.')])
        self.assertFormSetError(response, 'formset', 2, 'last_name', [_(u'This field is required.')])

        self.assertEqual(count, Contact.objects.count())

    def test_add_invalid_form(self):
        self.login()
        count = Contact.objects.count()

        data = self.quickform_data(1)
        self.quickform_data_append(data, 0, email='invalid')

        response = self.assertPOST200(self._build_quickform_url(Contact), data)
        self.assertFormError(response, 'form', 'last_name', _(u'This field is required.'))
        self.assertFormError(response, 'form', 'email',     _(u'Enter a valid email address.'))

        self.assertFormSetError(response, 'formset', 0, 'last_name', [_(u'This field is required.')])
        self.assertEqual(count, Contact.objects.count())

    def test_add_multiple_invalid_form(self):
        self.login()
        count = Contact.objects.count()

        data = self.quickform_data(3)
        self.quickform_data_append(data, 0, last_name='Kirika', email='admin@hello.com')
        self.quickform_data_append(data, 1, email='invalid')
        self.quickform_data_append(data, 2, last_name='Mireille', email='invalid')

        response = self.assertPOST200(self._build_quickform_url(Contact, 3), data)
        self.assertFormSetError(response, 'formset', 0, 'last_name')
        self.assertFormSetError(response, 'formset', 0, 'email')

        self.assertFormSetError(response, 'formset', 1, 'last_name', [_(u'This field is required.')])
        self.assertFormSetError(response, 'formset', 1, 'email', [_(u'Enter a valid email address.')])

        self.assertFormSetError(response, 'formset', 2, 'last_name')
        self.assertFormSetError(response, 'formset', 2, 'email', [_(u'Enter a valid email address.')])

        self.assertEqual(count, Contact.objects.count())

    def test_add(self):
        self.login()
        count = Contact.objects.count()

        data = self.quickform_data(1)
        last_name = 'Kirika'
        email = 'admin@hello.com'
        self.quickform_data_append(data, 0, last_name=last_name, email=email)

        self.assertPOST200(self._build_quickform_url(Contact), data)
        self.assertEqual(count + 1, Contact.objects.count())
        self.get_object_or_fail(Contact, last_name=last_name, email=email)

    def test_add_multiple(self):
        self.login()
        count = Contact.objects.count()

        contacts = [{'last_name': t[0], 'email': t[1]}
                        for t in [('Kirika',   'admin@hello.com'),
                                  ('Mireille', 'admin2@hello.com'),
                                  ('Chloe',    'admin3@hello.com'),
                                 ]
                   ]
        length = len(contacts)
        data = self.quickform_data(length)

        for i, kwargs in enumerate(contacts):
            self.quickform_data_append(data, i, **kwargs)

        self.assertPOST200(self._build_quickform_url(Contact, length), data)
        self.assertEqual(count + length, Contact.objects.count())

        for kwargs in contacts:
            self.get_object_or_fail(Contact, **kwargs)

    def test_add_from_widget(self):
        user = self.login()
        count = Contact.objects.count()

        last_name = 'Kirika'
        email = 'admin@hello.com'
        response = self.assertPOST200('/creme_core/quickforms/from_widget/%d/add/1' %
                                        ContentType.objects.get_for_model(Contact).pk,
                                      data={'last_name': last_name,
                                            'email':     email,
                                            'user':      user.id,
                                           }
                                     )
        self.assertEqual(count + 1, Contact.objects.count())

        contact = self.get_object_or_fail(Contact, last_name=last_name, email=email)
        self.assertEqual('<json>%s</json>' % JSONEncoder().encode({
                                "added": [[contact.id, unicode(contact)]], 
                                "value": contact.id
                            }),
                         response.content
                        )

    #TODO : test_add_multiple_from_widget(self)
