# -*- coding: utf-8 -*-

from django.test import TestCase
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType

from creme_core.models import RelationType, Relation, CremeProperty
from creme_core.management.commands.creme_populate import Command as PopulateCommand
from creme_core.constants import PROP_IS_MANAGED_BY_CREME

from persons.models import *
from persons.constants import *


class PersonsTestCase(TestCase):
    def login(self):
        if not self.user:
            user = User.objects.create(username='Kaneda')
            user.set_password(self.password)
            user.is_superuser = True
            user.save()
            self.user = user

        logged = self.client.login(username=self.user.username, password=self.password)
        self.assert_(logged, 'Not logged in')

    def setUp(self):
        PopulateCommand().handle(application=['creme_core', 'persons'])
        self.password = 'test'
        self.user = None

    def test_populate(self): #test relationtype creation with constraints
        def get_relationtype_or_fail(pk):
            try:
                return RelationType.objects.get(pk=pk)
            except RelationType.DoesNotExist:
                self.fail('Bad populate: unfoundable RelationType with pk=%s' % pk)

        rel_sub_employed = get_relationtype_or_fail(REL_SUB_EMPLOYED_BY)
        rel_obj_employed = get_relationtype_or_fail(REL_OBJ_EMPLOYED_BY)
        rel_sub_customer = get_relationtype_or_fail(REL_SUB_CUSTOMER_OF)
        rel_obj_customer = get_relationtype_or_fail(REL_OBJ_CUSTOMER_OF)

        self.assertEqual(rel_sub_employed.symmetric_type_id, rel_obj_employed.id)
        self.assertEqual(rel_obj_employed.symmetric_type_id, rel_sub_employed.id)

        get_ct = ContentType.objects.get_for_model
        ct_id_contact = get_ct(Contact).id
        ct_id_orga    = get_ct(Organisation).id
        self.assertEqual([ct_id_contact], [ct.id for ct in rel_sub_employed.subject_ctypes.all()])
        self.assertEqual([ct_id_orga],    [ct.id for ct in rel_obj_employed.subject_ctypes.all()])

        ct_id_set = set((ct_id_contact, ct_id_orga))
        self.assertEqual(ct_id_set, set(ct.id for ct in rel_sub_customer.subject_ctypes.all()))
        self.assertEqual(ct_id_set, set(ct.id for ct in rel_obj_customer.subject_ctypes.all()))

    def create_contact(self, first_name, last_name): #useful ??
        response = self.client.post('/persons/contact/add', follow=True,
                                    data={
                                            'user':       self.user.pk,
                                            'first_name': first_name,
                                            'last_name':  last_name,
                                         }
                                   )
        self.assertEqual(response.status_code, 200)

        return response

    def test_contact_createview01(self):
        self.login()

        response = self.client.get('/persons/contact/add')
        self.assertEqual(response.status_code, 200)

        count = Contact.objects.count()
        first_name = 'Spike'
        last_name  = 'Spiegel'
        response = self.create_contact(first_name, last_name)
        self.assertEqual(count + 1, Contact.objects.count())

        try:
            contact = Contact.objects.get(first_name=first_name)
        except Exception, e:
            self.fail(str(e))
        self.assertEqual(last_name,  contact.last_name)

        self.assert_(response.redirect_chain)
        self.assertEqual(len(response.redirect_chain), 1)
        self.assert_(response.redirect_chain[0][0].endswith('/persons/contact/%s' % contact.id))

    def test_orga_createview01(self):
        self.login()

        response = self.client.get('/persons/organisation/add')
        self.assertEqual(response.status_code, 200)

        count = Organisation.objects.count()
        name  = 'Spectre'
        description = 'DESCRIPTION'
        response = self.client.post('/persons/organisation/add', follow=True,
                                    data={
                                            'user':        self.user.pk,
                                            'name':        name,
                                            'description': description,
                                         }
                                   )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(count + 1, Organisation.objects.count())

        try:
            orga = Organisation.objects.get(name=name)
        except Exception, e:
            self.fail(str(e))
        self.assertEqual(description,  orga.description)

        self.assert_(response.redirect_chain)
        self.assertEqual(len(response.redirect_chain), 1)
        self.assert_(response.redirect_chain[0][0].endswith('/persons/organisation/%s' % orga.id))

    def test_orga_editview01(self):
        self.login()

        name = 'Bebop'
        orga = Organisation.objects.create(user=self.user, name=name)

        response = self.client.get('/persons/organisation/edit/%s' % orga.id)
        self.assertEqual(response.status_code, 200)

        name += '_edited'
        response = self.client.post('/persons/organisation/edit/%s' % orga.id, follow=True,
                                    data={
                                            'user': self.user.pk,
                                            'name': name,
                                         }
                                   )
        self.assertEqual(response.status_code, 200)
        self.assert_(response.redirect_chain)

        edited_orga = Organisation.objects.get(pk=orga.id)
        self.assertEqual(name, edited_orga.name)

    def test_become_customer(self):
        self.login()

        try:
            mng_orga = Organisation.objects.create(user=self.user, name='Bebop')
            CremeProperty.objects.create(type_id=PROP_IS_MANAGED_BY_CREME, creme_entity=mng_orga)
        except IndexError, e:
            self.fail(str(e))

        customer = Contact.objects.create(user=self.user, first_name='Jet', last_name='Black')

        response = self.client.get('/persons/%s/become_customer/%s' % (customer.id, mng_orga.id), follow=True)
        self.assertEqual(200, response.status_code)
        self.assert_(response.redirect_chain)

        try:
            Relation.objects.get(subject_entity=customer, object_entity=mng_orga, type=REL_SUB_CUSTOMER_OF)
        except Exception, e:
            self.fail(str(e))


#TODO: tests for edit/delete/detail/list views ; tests for Address model ; test leads_customers view
