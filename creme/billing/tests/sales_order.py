# -*- coding: utf-8 -*-

try:
    from datetime import date
    from decimal import Decimal

    from creme.creme_core.models import Currency

    from creme.persons.tests.base import skipIfCustomOrganisation, skipIfCustomAddress

    from ..models import SalesOrderStatus, SalesOrder
    from ..constants import REL_SUB_BILL_ISSUED, REL_SUB_BILL_RECEIVED
    from .base import _BillingTestCase
except Exception as e:
    print('Error in <%s>: %s' % (__name__, e))


__all__ = ('SalesOrderTestCase',)


@skipIfCustomOrganisation
class SalesOrderTestCase(_BillingTestCase):
    def setUp(self):
        #_BillingTestCase.setUp(self)
        self.login()

    def create_salesorder(self, name, source, target, currency=None, status=None): #TODO inline (used once)
        currency = currency or Currency.objects.all()[0]
        response = self.client.post('/billing/sales_order/add', follow=True,
                                    data={'user':            self.user.pk,
                                          'name':            name,
                                          'issuing_date':    '2012-1-5',
                                          'expiration_date': '2012-2-15',
                                          'status':          status.id if status else 1,
                                          'currency':        currency.id,
                                          'discount':        Decimal(),
                                          'source':          source.id,
                                          'target':          self.genericfield_format_entity(target),
                                         }
                                   )
        self.assertNoFormError(response)

        return self.get_object_or_fail(SalesOrder, name=name)

    def create_salesorder_n_orgas(self, name, currency=None, status=None):
        source, target = self.create_orgas()
        order = self.create_salesorder(name, source, target, currency, status)

        return order, source, target

    def test_createview01(self):
        self.assertGET200('/billing/sales_order/add')

        currency = Currency.objects.all()[0]
        status   = SalesOrderStatus.objects.all()[1]
        order, source, target = self.create_salesorder_n_orgas('My Sales Order', currency, status)
        self.assertEqual(date(year=2012, month=1, day=5),  order.issuing_date)
        self.assertEqual(date(year=2012, month=2, day=15), order.expiration_date)
        self.assertEqual(currency,                         order.currency)
        self.assertEqual(status,                           order.status)

        self.assertRelationCount(1, order, REL_SUB_BILL_ISSUED,   source)
        self.assertRelationCount(1, order, REL_SUB_BILL_RECEIVED, target)

    def test_create_linked(self):
        source, target = self.create_orgas()
        url = '/billing/sales_order/add/%s/source/%s' % (target.id, source.id)
        response = self.assertGET200(url)

        with self.assertNoException():
            form = response.context['form']

        self.assertEqual({'status': 1, 'source': str(source.id), 'target': target},
                         form.initial
                        )

        name = 'Order#1'
        currency = Currency.objects.all()[0]
        status   = SalesOrderStatus.objects.all()[1]
        response = self.client.post(url, follow=True,
                                    data={'user':            self.user.pk,
                                          'name':            name,
                                          'issuing_date':    '2013-12-13',
                                          'expiration_date': '2014-1-20',
                                          'status':          status.id,
                                          'currency':        currency.id,
                                          'discount':        Decimal(),
                                          'source':          source.id,
                                          'target':          self.genericfield_format_entity(target),
                                         }
                                   )
        self.assertNoFormError(response)

        order = self.get_object_or_fail(SalesOrder, name=name)
        self.assertEqual(date(year=2013, month=12, day=13), order.issuing_date)
        self.assertEqual(date(year=2014, month=1,  day=20), order.expiration_date)
        self.assertEqual(currency,                         order.currency)
        self.assertEqual(status,                           order.status)

        self.assertRelationCount(1, order, REL_SUB_BILL_ISSUED,   source)
        self.assertRelationCount(1, order, REL_SUB_BILL_RECEIVED, target)

    def test_editview(self):
        name = 'my sales order'
        order, source, target = self.create_salesorder_n_orgas(name)

        url = order.get_edit_absolute_url()
        self.assertGET200(url)

        name     = name.title()
        currency = Currency.objects.create(name=u'Marsian dollar', local_symbol=u'M$', international_symbol=u'MUSD', is_custom=True)
        status   = SalesOrderStatus.objects.all()[1]
        response = self.client.post(url, follow=True,
                                    data={'user':            self.user.pk,
                                          'name':            name,
                                          'issuing_date':    '2012-2-12',
                                          'expiration_date': '2012-3-13',
                                          'status':          status.id,
                                          'currency':        currency.id,
                                          'discount':        Decimal(),
                                          'source':          source.id,
                                          'target':          self.genericfield_format_entity(target),
                                         }
                                   )
        self.assertNoFormError(response)

        order = self.refresh(order)
        self.assertEqual(name,                             order.name)
        self.assertEqual(date(year=2012, month=2, day=12), order.issuing_date)
        self.assertEqual(date(year=2012, month=3, day=13), order.expiration_date)
        self.assertEqual(currency,                         order.currency)
        self.assertEqual(status,                           order.status)

    def test_listview(self):
        order1 = self.create_salesorder_n_orgas('Order1')[0]
        order2 = self.create_salesorder_n_orgas('Order2')[0]

        response = self.assertGET200('/billing/sales_orders')

        with self.assertNoException():
            orders_page = response.context['entities']

        self.assertEqual(2, orders_page.paginator.count)
        self.assertEqual({order1, order2}, set(orders_page.paginator.object_list))

    def test_delete_status01(self):
        status = SalesOrderStatus.objects.create(name='OK')
        self.assertDeleteStatusOK(status, 'sales_order_status')

    def test_delete_status02(self):
        status = SalesOrderStatus.objects.create(name='OK')
        order = self.create_salesorder_n_orgas('Order', status=status)[0]

        self.assertDeleteStatusKO(status, 'sales_order_status', order)

    @skipIfCustomAddress
    def test_csv_import(self):
        self._aux_test_csv_import(SalesOrder, SalesOrderStatus)

    @skipIfCustomAddress
    def test_csv_import_update(self):
        self._aux_test_csv_import_update(SalesOrder, SalesOrderStatus)
