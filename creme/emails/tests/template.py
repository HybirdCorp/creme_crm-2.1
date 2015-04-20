# -*- coding: utf-8 -*-

try:
    from django.utils.translation import ugettext as _

    from .base import _EmailsTestCase
    from ..models import EmailTemplate
except Exception as e:
    print('Error in <%s>: %s' % (__name__, e))


__all__ = ('TemplatesTestCase',)


class TemplatesTestCase(_EmailsTestCase):
    def setUp(self):
        self.login()

    def test_createview01(self): #TODO: test attachments & images
        url = '/emails/template/add'
        self.assertGET200(url)

        name      = 'my_template'
        subject   = 'Insert a joke *here*'
        body      = 'blablabla {{first_name}}'
        body_html = '<p>blablabla {{last_name}}</p>'
        response = self.client.post(url, follow=True,
                                    data={'user':      self.user.pk,
                                          'name':      name,
                                          'subject':   subject,
                                          'body':      body,
                                          'body_html': body_html,
                                         }
                                   )
        self.assertNoFormError(response)

        template = self.get_object_or_fail(EmailTemplate, name=name)
        self.assertEqual(subject,   template.subject)
        self.assertEqual(body,      template.body)
        self.assertEqual(body_html, template.body_html)

    def test_createview02(self):
        "Validation error"
        response = self.assertPOST200('/emails/template/add', follow=True,
                                      data={'user':      self.user.pk,
                                            'name':      'my_template',
                                            'subject':   'Insert a joke *here*',
                                            'body':      'blablabla {{unexisting_var}}',
                                            'body_html': '<p>blablabla</p> {{foobar_var}}',
                                           }
                                   )

        #error_msg = _(u'The following variables are invalid: %s')
        #self.assertFormError(response, 'form', 'body',      [error_msg % [u'unexisting_var']])
        #self.assertFormError(response, 'form', 'body_html', [error_msg % [u'foobar_var']])
        error_msg = _(u'The following variables are invalid: %(vars)s')
        self.assertFormError(response, 'form', 'body',
                             error_msg % {'vars': [u'unexisting_var']}
                            )
        self.assertFormError(response, 'form', 'body_html',
                             error_msg % {'vars': [u'foobar_var']}
                            )

    def test_editview01(self):
        name    = 'my template'
        subject = 'Insert a joke *here*'
        body    = 'blablabla'
        template = EmailTemplate.objects.create(user=self.user, name=name, subject=subject, body=body)

        url = '/emails/template/edit/%s' % template.id
        self.assertGET200(url)

        name    = name.title()
        subject = subject.title()
        body    += ' edited'
        response = self.client.post(url, follow=True,
                                    data={'user':    self.user.pk,
                                          'name':    name,
                                          'subject': subject,
                                          'body':    body,
                                         }
                                   )
        self.assertNoFormError(response)

        template = self.refresh(template)
        self.assertEqual(name,    template.name)
        self.assertEqual(subject, template.subject)
        self.assertEqual(body,    template.body)
        self.assertEqual('',      template.body_html)

    def test_listview(self):
        response = self.assertGET200('/emails/templates')

        with self.assertNoException():
            response.context['entities']


