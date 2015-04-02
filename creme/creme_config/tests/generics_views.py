# -*- coding: utf-8 -*-

try:
    from django.contrib.contenttypes.models import ContentType
    from django.core.serializers.json import DjangoJSONEncoder as JSONEncoder, simplejson

    from creme.creme_core.tests.base import CremeTestCase

    from creme.persons.models import Civility

    from creme.billing.models import InvoiceStatus

    from ..blocks import generic_models_block
except Exception as e:
    print('Error in <%s>: %s' % (__name__, e))


__all__ = ('GenericModelConfigTestCase',)


#NB: see Opportunities for tests on 'up' & 'down' views
class GenericModelConfigTestCase(CremeTestCase):
    @classmethod
    def setUpClass(cls):
        CremeTestCase.setUpClass()
        cls.populate('creme_core')

    def setUp(self):
        self.login()

    def test_portals(self):
        self.assertGET200('/creme_config/persons/portal/')
        self.assertGET404('/creme_config/unexsitingapp/portal/')

        self.assertGET200('/creme_config/persons/civility/portal/')
        self.assertGET404('/creme_config/persons/unexistingmodel/portal/')

        self.assertGET200('/creme_config/billing/invoice_status/portal/')

    def test_add01(self):
        count = Civility.objects.count()

        url = '/creme_config/persons/civility/add/'
        self.assertGET200(url)

        title = 'Generalissime'
        shortcut = 'G.'
        self.assertNoFormError(self.client.post(url, data={'title': title, 'shortcut': shortcut}))
        self.assertEqual(count + 1, Civility.objects.count())
        civility = self.get_object_or_fail(Civility, title=title)
        self.assertEqual(shortcut, civility.shortcut)

    def test_add02(self):
        count = InvoiceStatus.objects.count()

        url = '/creme_config/billing/invoice_status/add/'
        self.assertGET200(url)

        name = 'Okidoki'
        self.assertNoFormError(self.client.post(url, data={'name': name}))
        self.assertEqual(count + 1, InvoiceStatus.objects.count())

        status = self.get_object_or_fail(InvoiceStatus, name=name, is_custom=True)
        self.assertEqual(count + 1, status.order) #order is set to max

        name = 'Youkaidi'
        self.client.post(url, data={'name': name})
        status = self.get_object_or_fail(InvoiceStatus, name=name)
        self.assertEqual(count + 2, status.order) #order is set to max

    def assertWidgetResponse(self, response, instance):
        self.assertEqual(u'<json>%s</json>' % JSONEncoder().encode({
                            'added': [[instance.id, unicode(instance)]], 
                            'value': instance.id
                         }), 
                         response.content
                        )

    def test_add01_from_widget(self):
        count = Civility.objects.count()

        url = '/creme_config/persons/civility/add_widget/'
        self.assertGET200(url)

        title = 'Generalissime'
        shortcut = 'G.'
        response = self.client.post(url, data={'title': title, 'shortcut': shortcut})
        self.assertNoFormError(response)
        self.assertEqual(count + 1, Civility.objects.count())

        civility = self.get_object_or_fail(Civility, title=title)
        self.assertEqual(shortcut, civility.shortcut)
        self.assertWidgetResponse(response, civility)

    def test_add02_from_widget(self):
        count = InvoiceStatus.objects.count()

        url = '/creme_config/billing/invoice_status/add_widget/'
        self.assertGET200(url)

        name = 'Okidoki'
        response = self.client.post(url, data={'name': name})
        self.assertNoFormError(response)
        self.assertEqual(count + 1, InvoiceStatus.objects.count())

        status = self.get_object_or_fail(InvoiceStatus, name=name, is_custom=True)
        self.assertEqual(count + 1, status.order) #order is set to max
        self.assertWidgetResponse(response, status)

        name = 'Youkaidi'
        response = self.client.post(url, data={'name': name})
        status = self.get_object_or_fail(InvoiceStatus, name=name)
        self.assertEqual(count + 2, status.order) #order is set to max
        self.assertWidgetResponse(response, status)

    def test_edit01(self):
        title = 'herr'
        shortcut = 'H.'
        civ = Civility.objects.create(title=title, shortcut=shortcut)

        url = '/creme_config/persons/civility/edit/%s' % civ.id
        self.assertGET200(url)

        title = title.title()
        self.assertNoFormError(self.client.post(url, data={'title': title, 'shortcut': shortcut}))

        civ = self.refresh(civ)
        self.assertEqual(title,    civ.title)
        self.assertEqual(shortcut, civ.shortcut)

    def test_edit02(self):
        "Order not changed"
        count = InvoiceStatus.objects.count()

        create_status = InvoiceStatus.objects.create
        status1 = create_status(name='okidoki',  order=count + 1)
        #status2 = create_status(name='Youkaidi', order=count + 2)

        url = '/creme_config/billing/invoice_status/edit/%s' % status1.id
        self.assertGET200(url)

        name = status1.name.title()
        self.assertNoFormError(self.client.post(url, data={'name': name}))

        new_status1 = self.refresh(status1)
        self.assertEqual(name,          new_status1.name)
        self.assertEqual(status1.order, new_status1.order)

    def test_delete01(self):
        civ = Civility.objects.create(title='Herr')
        url = '/creme_config/persons/civility/delete'
        data = {'id': civ.pk}
        self.assertGET404(url, data=data)
        self.assertPOST200(url, data=data)
        self.assertDoesNotExist(civ)

    def test_delete02(self):
        "Not custom instance"
        status = InvoiceStatus.objects.create(name='Okidoki', is_custom=False)
        self.assertPOST404('/creme_config/billing/invoice_status/delete', data={'id': status.pk})
        self.assertStillExists(status)

    def test_reload_block(self):
        response = self.assertGET200('/creme_config/models/%s/reload/' %
                                        ContentType.objects.get_for_model(Civility).id
                                    )

        with self.assertNoException():
            result = simplejson.loads(response.content)

        self.assertIsInstance(result, list)
        self.assertEqual(1, len(result))

        result = result[0]
        self.assertIsInstance(result, list)
        self.assertEqual(2, len(result))
        self.assertEqual(generic_models_block.id_, result[0])
        self.assertIn(' id="%s"' % generic_models_block.id_, result[1])
