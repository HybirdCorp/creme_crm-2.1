# -*- coding: utf-8 -*-

try:
    from django.contrib.contenttypes.models import ContentType

    from creme_core.tests.base import CremeTestCase

    from persons.models import Address, Organisation, Contact
    from persons.blocks import other_address_block
except Exception as e:
    print 'Error in <%s>: %s' % (__name__, e)


__all__ = ('AddressTestCase',)


class AddressTestCase(CremeTestCase):
    @classmethod
    def setUpClass(cls):
        cls.populate('creme_config', 'creme_core', 'persons')

    def login(self, *args, **kwargs):
        super(AddressTestCase, self).login(*args, **kwargs)

        return Organisation.objects.create(user=self.user, name='Nerv')

    def _create_address(self, orga, name, address, po_box, city, state, zipcode, country, department):
        response = self.client.post('/persons/address/add/%s' % orga.id,
                                    data={'name':       name,
                                          'address':    address,
                                          'po_box':     po_box,
                                          'city':       city,
                                          'state':      state,
                                          'zipcode':    zipcode,
                                          'country':    country,
                                          'department': department,
                                         }
                                   )
        self.assertEqual(response.status_code, 200)
        self.assertNoFormError(response)

    def test_createview(self):
        orga = self.login()
        self.assertEqual(0, Address.objects.filter(object_id=orga.id).count())

        response = self.client.get('/persons/address/add/%s' % orga.id)
        self.assertEqual(200, response.status_code)

        name = 'Address#1'
        address_value = '21 jump street'
        po_box = 'Popop'
        city = 'Atlantis'
        state = '??'
        zipcode = '424242'
        country = 'wtf'
        department = 'rucrazy'

        self._create_address(orga, name, address_value, po_box, city, state, zipcode, country, department)

        addresses = Address.objects.filter(object_id=orga.id)
        self.assertEqual(1, len(addresses))

        address = addresses[0]
        self.assertEqual(name,       address.name)
        self.assertEqual(address_value, address.address)
        self.assertEqual(po_box,     address.po_box)
        self.assertEqual(city,       address.city)
        self.assertEqual(state,      address.state)
        self.assertEqual(zipcode,    address.zipcode)
        self.assertEqual(country,    address.country)
        self.assertEqual(department, address.department)

        response = self.client.get(orga.get_absolute_url())
        self.assertContains(response, 'id="%s"' % other_address_block.id_)
        self.assertContains(response, name)
        self.assertContains(response, address_value)
        self.assertContains(response, po_box)
        self.assertContains(response, city)
        self.assertContains(response, state)
        self.assertContains(response, zipcode)
        self.assertContains(response, country)
        self.assertContains(response, department)

    def test_editview(self):
        orga = self.login()

        name = 'Address#1'
        address_value = '21 jump street'
        po_box = 'Popop'
        city = 'Atlantis'
        state = '??'
        zipcode = '424242'
        country = 'wtf'
        department = 'rucrazy'

        self._create_address(orga, name, address_value, po_box, city, state, zipcode, country, department)
        address = Address.objects.filter(object_id=orga.id)[0]

        url = '/persons/address/edit/%s' % address.id
        self.assertEqual(200, self.client.get(url).status_code)

        city = 'Groville'
        country = 'Groland'
        response = self.client.post(url, data={'name':       name,
                                               'address':    address,
                                               'po_box':     po_box,
                                               'city':       city,
                                               'state':      state,
                                               'zipcode':    zipcode,
                                               'country':    country,
                                               'department': department,
                                             }
                                   )
        self.assertEqual(200, response.status_code)
        self.assertNoFormError(response)

        address = self.refresh(address)
        self.assertEqual(city,    address.city)
        self.assertEqual(country, address.country)

    def test_deleteview(self):
        orga = self.login()

        self._create_address(orga, 'name', 'address', 'po_box', 'city', 'state', 'zipcode', 'country', 'department')
        address = Address.objects.filter(object_id=orga.id)[0]
        ct = ContentType.objects.get_for_model(Address)

        response = self.client.post('/creme_core/entity/delete_related/%s' % ct.id, data={'id': address.id})
        self.assertEqual(0, Address.objects.filter(object_id=orga.id).count())

    def test_bool(self):
        self.assertFalse(Address())
        self.assertTrue(Address(name='Address#1'))
        self.assertTrue(Address(address='21 jump street'))
        self.assertTrue(Address(po_box='Popop'))
        self.assertTrue(Address(zipcode='424242'))
        self.assertTrue(Address(city='Atlantis'))
        self.assertTrue(Address(department='rucrazy'))
        self.assertTrue(Address(state='OfTheArt'))
        self.assertTrue(Address(country='Yeeeha'))

        self.assertTrue(Address(address='21 jump street', country='Yeeeha'))

    def test_unicode(self):
        name = 'Address#1'
        address_value = '21 jump street'
        po_box = 'Popop'
        zipcode = '424242'
        city = 'Atlantis'
        department = 'rucrazy'
        state = '??'
        country = 'wtf'

        address = Address(name=name,
                          address=address_value,
                          po_box=po_box,
                          zipcode=zipcode,
                          city=city,
                          department=department,
                          state=state,
                          country=country
                         )
        self.assertEqual(u'%s %s %s %s' % (address_value, zipcode, city, department),
                         unicode(address)
                        )

        address.zipcode = None
        self.assertEqual(u'%s %s %s' % (address_value, city, department), unicode(address))

        address.department = None
        self.assertEqual(u'%s %s' % (address_value, city), unicode(address))

        self.assertEqual(po_box, unicode(Address(po_box=po_box)))
        self.assertEqual(state, unicode(Address(state=state)))
        self.assertEqual(country, unicode(Address(country=country)))

        self.assertEqual('%s %s %s' % (po_box, state, country),
                         unicode(Address(po_box=po_box, state=state, country=country))
                        )

    def test_delete_orga(self): #are addresses cleaned ?
        orga = self.login()

        create_address = Address.objects.create
        orga.billing_address = b_addr = create_address(name="Billing address",
                                                       address="BA - Address",
                                                       owner=orga,
                                                      )
        orga.save()

        orga.shipping_address = s_addr = create_address(name="Shipping address",
                                                        address="SA - Address",
                                                        owner=orga,
                                                       )
        orga.save()

        other_addr = create_address(name="Other address", address="OA - Address", owner=orga)

        orga.delete()
        self.assertFalse(Organisation.objects.filter(pk=orga.id).exists())
        self.assertFalse(Address.objects.filter(pk__in=[b_addr.id, s_addr.id, other_addr.id]))

    def test_delete_contact(self): #are addresses cleaned ?
        self.login()

        contact = Contact.objects.create(user=self.user, first_name='Rei', last_name='Ayanami')

        create_address = Address.objects.create
        contact.billing_address = b_addr = create_address(name="Billing address",
                                                          address="BA - Address",
                                                          owner=contact,
                                                         )
        contact.save()

        contact.shipping_address = s_addr = create_address(name="Shipping address",
                                                           address="SA - Address",
                                                           owner=contact,
                                                          )
        contact.save()

        other_addr = create_address(name="Other address", address="OA - Address", owner=contact)

        contact.delete()
        self.assertFalse(Contact.objects.filter(pk=contact.id).exists())
        self.assertFalse(Address.objects.filter(pk__in=[b_addr.id, s_addr.id, other_addr.id]))
