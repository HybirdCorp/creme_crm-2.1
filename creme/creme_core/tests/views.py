# -*- coding: utf-8 -*-

from django.test import TestCase
from django.core.serializers.json import simplejson
from django.utils.translation import ugettext as _
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType

from creme_core.models import *
from creme_core.management.commands.creme_populate import Command as PopulateCommand

from persons.models import Contact, Organisation #TODO: find a way to create model that inherit CremeEntity in the unit tests ??


class ViewsTestCase(TestCase):
    def login(self, is_superuser=True):
        password = 'test'

        superuser = User.objects.create(username='Kirika')
        superuser.set_password(password)
        superuser.is_superuser = True
        superuser.save()

        role = UserRole.objects.create(name='Basic')
        role.allowed_apps = ['creme_core']
        role.save()
        SetCredentials.objects.create(role=role,
                                      value=SetCredentials.CRED_VIEW,
                                      set_type=SetCredentials.ESET_OWN)
        basic_user = User.objects.create(username='Mireille', role=role)
        basic_user.set_password(password)
        basic_user.save()

        self.user, self.other_user = (superuser, basic_user) if is_superuser else \
                                     (basic_user, superuser)

        logged = self.client.login(username=self.user.username, password=password)
        self.assert_(logged, 'Not logged in')

    def test_clean(self):
        self.login()

        try:
            response = self.client.get('/creme_core/clean/', follow=True)
        except Exception, e:
            self.fail(str(e))

        self.assertEqual(200, response.status_code)
        self.assertEqual(2,   len(response.redirect_chain))

        last = response.redirect_chain[-1]
        self.assert_(last[0].endswith('/creme_login/'))
        self.assertEqual(302, last[1])

    def test_get_fields(self):
        self.login()

        ct_id = ContentType.objects.get_for_model(CremeEntity).id
        response = self.client.post('/creme_core/get_fields', data={'ct_id': ct_id})
        self.assertEqual(200,               response.status_code)
        self.assertEqual('text/javascript', response['Content-Type'])

        content = simplejson.loads(response.content)
        #print 'CONTENT:', content
        self.assertEqual(14, len(content))
        self.assertEqual(content[0], ["created",          "Creme entity - " + _('Creation date')])
        self.assertEqual(content[1], ["modified",         "Creme entity - " + _("Last modification")])
        self.assertEqual(content[2], ["user__id",         _("User") + " - Id"])
        self.assertEqual(content[3], ["user__username",   _("User") + " - " + _("Username")])
        self.assertEqual(content[4], ["user__first_name", _("User") + " - " + _("First name")])
        #etc...

        response = self.client.post('/creme_core/get_fields', data={'ct_id': 0})
        self.assertEqual(404,               response.status_code)
        self.assertEqual('text/javascript', response['Content-Type'])

        response = self.client.post('/creme_core/get_fields', data={'ct_id': 'notint'})
        self.assertEqual(400,               response.status_code)
        self.assertEqual('text/javascript', response['Content-Type'])

        response = self.client.post('/creme_core/get_fields', data={'ct_id': ct_id, 'deep': 'notint'})
        self.assertEqual(400,               response.status_code)
        self.assertEqual('text/javascript', response['Content-Type'])

    def test_get_function_fields(self):
        self.login()

        ct_id = ContentType.objects.get_for_model(CremeEntity).id
        response = self.client.post('/creme_core/get_function_fields', data={'ct_id': ct_id})
        self.assertEqual(200,               response.status_code)
        self.assertEqual('text/javascript', response['Content-Type'])

        content = simplejson.loads(response.content)
        self.assertEqual(content, [['get_pretty_properties', _('Properties')]])

        response = self.client.post('/creme_core/get_function_fields', data={'ct_id': 0})
        self.assertEqual(404,               response.status_code)
        self.assertEqual('text/javascript', response['Content-Type'])

        response = self.client.post('/creme_core/get_function_fields', data={'ct_id': 'notint'})
        self.assertEqual(400,               response.status_code)
        self.assertEqual('text/javascript', response['Content-Type'])

    def test_get_custom_fields(self):
        self.login()

        ct = ContentType.objects.get_for_model(CremeEntity)
        response = self.client.post('/creme_core/get_custom_fields', data={'ct_id': ct.id})
        self.assertEqual(200,               response.status_code)
        self.assertEqual('text/javascript', response['Content-Type'])
        self.assertEqual([], simplejson.loads(response.content))

        CustomField.objects.create(name='cf01', content_type=ct, field_type=CustomField.INT)
        CustomField.objects.create(name='cf02', content_type=ct, field_type=CustomField.FLOAT)

        response = self.client.post('/creme_core/get_custom_fields', data={'ct_id': ct.id})
        self.assertEqual([['cf01', 'cf01'], ['cf02', 'cf02']], simplejson.loads(response.content))

        response = self.client.post('/creme_core/get_custom_fields', data={'ct_id': 0})
        self.assertEqual(404,               response.status_code)
        self.assertEqual('text/javascript', response['Content-Type'])

        response = self.client.post('/creme_core/get_custom_fields', data={'ct_id': 'notint'})
        self.assertEqual(400,               response.status_code)
        self.assertEqual('text/javascript', response['Content-Type'])

    def test_get_creme_entity_as_json01(self):
        self.login()

        try:
            entity = CremeEntity.objects.create(user=self.user)
        except Exception, e:
            self.fail(str(e))

        response = self.client.post('/creme_core/entity/json', data={'pk': entity.id})
        self.assertEqual(200,               response.status_code)
        self.assertEqual('text/javascript', response['Content-Type'])

        json_data = simplejson.loads(response.content)
        #[{'pk': 1,
        #  'model': 'creme_core.cremeentity',
        #  'fields': {'is_actived': False,
        #             'is_deleted': False,
        #             'created': '2010-11-09 14:34:04',
        #             'header_filter_search_field': '',
        #             'entity_type': 100,
        #             'modified': '2010-11-09 14:34:04',
        #             'user': 1
        #            }
        #}]
        try:
            dic = json_data[0]
            pk     = dic['pk']
            model  = dic['model']
            fields = dic['fields']
            user = fields['user']
        except Exception, e:
            self.fail(str(e))

        self.assertEqual(entity.id, pk)
        self.assertEqual('creme_core.cremeentity', model)
        self.assertEqual(self.user.id, user)

    def test_get_creme_entity_as_json02(self):
        self.login()

        try:
            entity = CremeEntity.objects.create(user=self.user)
        except Exception, e:
            self.fail(str(e))

        response = self.client.post('/creme_core/entity/json', data={'pk': entity.id, 'fields': ['user', 'entity_type']})
        self.assertEqual(200, response.status_code)

        json_data = simplejson.loads(response.content)
        #[{'pk': 1,
        #  'model': 'creme_core.cremeentity',
        #  'fields': {'user': 1, 'entity_type': 100}}
        #]
        try:
            fields = json_data[0]['fields']
            user = fields['user']
            entity_type = fields['entity_type']
        except Exception, e:
            self.fail(str(e))

            self.assertEqual(self.user.id, user)
            self.assertEqual(ContentType.objects.get_for_model(CremeEntity).id, entity_type)

    def test_get_creme_entity_repr(self):
        self.login()

        try:
            entity = CremeEntity.objects.create(user=self.user)
        except Exception, e:
            self.fail(str(e))

        response = self.client.get('/creme_core/entity/get_repr/%s' % entity.id)
        self.assertEqual(200,               response.status_code)
        self.assertEqual('text/javascript', response['Content-Type'])
        self.assertEqual('Creme entity: %s' % entity.id, response.content)

    def test_add_property(self):
        self.login()

        ptype01 = CremePropertyType.create(str_pk='test-prop_foobar01', text='wears strange hats')
        ptype02 = CremePropertyType.create(str_pk='test-prop_foobar02', text='wears strange pants')
        entity  = CremeEntity.objects.create(user=self.user)
        self.assertEqual(0, entity.properties.count())

        response = self.client.get('/creme_core/property/add/%s' % entity.id)
        self.assertEqual(200, response.status_code)

        response = self.client.post('/creme_core/property/add/%s' % entity.id,
                                    data={'types': [ptype01.id, ptype02.id]}
                                   )
        self.assertEqual(200, response.status_code)

        properties = entity.properties.all()
        self.assertEqual(2, len(properties))
        self.assertEqual(set([ptype01.id, ptype02.id]), set(p.type_id for p in properties))

    def test_delete_property(self):
        self.login()

        ptype  = CremePropertyType.create(str_pk='test-prop_foobar', text='hairy')
        entity = CremeEntity.objects.create(user=self.user)
        prop   = CremeProperty.objects.create(type=ptype, creme_entity=entity)

        response = self.client.post('/creme_core/property/delete', data={'id': prop.id})
        self.assertEqual(302, response.status_code)
        self.assertEqual(0,   CremeProperty.objects.filter(pk=prop.id).count())

    #TODO: test get_property_types_for_ct(), add_to_entities()

    def _aux_relation_objects_to_link_selection(self):
        PopulateCommand().handle(application=['creme_core', 'persons'])

        self.login()

        self.assertEqual(1, Contact.objects.count())
        self.contact01 = Contact.objects.all()[0] #NB: Fulbert Creme

        self.subject   = CremeEntity.objects.create(user=self.user)
        self.contact02 = Contact.objects.create(user=self.user, first_name='Laharl', last_name='Overlord')
        self.contact03 = Contact.objects.create(user=self.user, first_name='Etna',   last_name='Devil')
        self.orga01    = Organisation.objects.create(user=self.user, name='Earth Defense Force')

        self.rtype, sym_rtype = RelationType.create(('test-subject_foobar', 'is loving',   [Contact]),
                                               ('test-object_foobar',  'is loved by', [Contact])
                                              )

    def test_relation_objects_to_link_selection01(self):
        self._aux_relation_objects_to_link_selection()

        ct = ContentType.objects.get_for_model(Contact)
        response = self.client.get('/creme_core/relation/objects2link/rtype/%s/entity/%s/%s' % \
                                        (self.rtype.id, self.subject.id, ct.id)
                                  )
        self.assertEqual(200, response.status_code)

        try:
            entities = response.context['entities']
        except Exception, e:
            self.fail('%s : %s' % (e.__class__.__name__, str(e)))

        contacts = entities.object_list
        self.assertEqual(3, len(contacts))
        self.assert_(all(isinstance(c, Contact) for c in contacts))
        self.assertEqual(set([self.contact01.id, self.contact02.id, self.contact03.id]),
                         set(c.id for c in contacts)
                        )

    def _aux_add_relations_with_same_type(self):
        self.subject  = CremeEntity.objects.create(user=self.user)
        self.object01 = CremeEntity.objects.create(user=self.user)
        self.object02 = CremeEntity.objects.create(user=self.user)
        self.rtype, sym_rtype = RelationType.create(('test-subject_foobar', 'is loving',),
                                                    ('test-object_foobar',  'is loved by',)
                                                   )

    def test_add_relations_with_same_type01(self): #no errors
        self.login()
        self._aux_add_relations_with_same_type()

        object_ids = [self.object01.id, self.object02.id]
        response = self.client.post('/creme_core/relation/add_from_predicate/save',
                                    data={
                                            'subject_id':   self.subject.id,
                                            'predicate_id': self.rtype.id,
                                            'entities':     object_ids,
                                         }
                                   )
        self.assertEqual(200, response.status_code)
        self.assertEqual(2,   Relation.objects.filter(type=self.rtype.id).count())

        relations = self.subject.relations.filter(type=self.rtype.id)
        self.assertEqual(2, len(relations))
        self.assertEqual(set(object_ids), set(r.object_entity_id for r in relations))

    def test_add_relations_with_same_type02(self): #an entity does not exist
        self.login()
        self._aux_add_relations_with_same_type()

        response = self.client.post('/creme_core/relation/add_from_predicate/save',
                                    data={
                                            'subject_id':   self.subject.id,
                                            'predicate_id': self.rtype.id,
                                            'entities':     [self.object01.id, self.object02.id, self.object02.id + 1],
                                         }
                                   )
        self.assertEqual(404, response.status_code)
        self.assertEqual(2,   Relation.objects.filter(type=self.rtype.id).count())

    def test_add_relations_with_same_type03(self): #errors
        self.login()
        self._aux_add_relations_with_same_type()
        post = self.client.post

        self.assertEqual(404, post('/creme_core/relation/add_from_predicate/save',
                                    data={
                                            'subject_id':   self.subject.id,
                                            'predicate_id': 'IDONOTEXIST',
                                            'entities':     [self.object01.id],
                                         }
                                  ).status_code
                        )
        self.assertEqual(404, post('/creme_core/relation/add_from_predicate/save',
                                    data={
                                            'subject_id':   1024,
                                            'predicate_id': self.rtype.id,
                                            'entities':     [self.object01.id],
                                         }
                                  ).status_code
                        )
        self.assertEqual(404, post('/creme_core/relation/add_from_predicate/save',
                                    data={
                                            'predicate_id': self.rtype.id,
                                            'entities':     [self.object01.id],
                                         }
                                  ).status_code
                        )
        self.assertEqual(404, post('/creme_core/relation/add_from_predicate/save',
                                    data={
                                            'subject_id': self.subject.id,
                                            'entities':   [self.object01.id],
                                         }
                                  ).status_code
                        )
        self.assertEqual(404, post('/creme_core/relation/add_from_predicate/save',
                                    data={
                                            'subject_id':   self.subject.id,
                                            'predicate_id': self.rtype.id,
                                         }
                                  ).status_code
                        )

    def test_add_relations_with_same_type04(self): #credentials errors
        self.login(is_superuser=False)

        forbidden = CremeEntity.objects.create(user=self.other_user)
        allowed01 = CremeEntity.objects.create(user=self.user)
        allowed02 = CremeEntity.objects.create(user=self.user)
        rtype, sym_rtype = RelationType.create(('test-subject_foobar', 'is loving',),
                                               ('test-object_foobar',  'is loved by',)
                                              )

        post = self.client.post

        self.failIf(forbidden.can_view(self.user))
        self.assert_(allowed01.can_view(self.user))

        self.assertEqual(403, post('/creme_core/relation/add_from_predicate/save',
                                    data={
                                            'subject_id':   forbidden.id,
                                            'predicate_id': rtype.id,
                                            'entities':     [allowed01.id, allowed02.id],
                                         }
                                  ).status_code
                        )
        self.assertEqual(0, Relation.objects.filter(type=rtype.id).count())

        self.assertEqual(403, post('/creme_core/relation/add_from_predicate/save',
                                    data={
                                            'subject_id':   allowed01.id,
                                            'predicate_id': rtype.id,
                                            'entities':     [forbidden.id, allowed02.id, 1024],
                                         }
                                  ).status_code
                        )
        relations = Relation.objects.filter(type=rtype.id)
        self.assertEqual(1, len(relations))

        relation = relations[0]
        self.assertEqual(allowed01.id, relation.subject_entity_id)
        self.assertEqual(allowed02.id, relation.object_entity_id)

    def test_relation_objects_to_link_selection02(self):
        self._aux_relation_objects_to_link_selection()

        #contact03 will not be proposed by the listview
        Relation.objects.create(user=self.user, type=self.rtype, subject_entity=self.subject, object_entity=self.contact03)

        ct = ContentType.objects.get_for_model(Contact)
        response = self.client.get('/creme_core/relation/objects2link/rtype/%s/entity/%s/%s' % \
                                        (self.rtype.id, self.subject.id, ct.id)
                                  )
        self.assertEqual(200, response.status_code)

        contacts = response.context['entities'].object_list
        self.assertEqual(2, len(contacts))
        self.assertEqual(set([self.contact01.id, self.contact02.id]), set(c.id for c in contacts))

    def test_add_relations_with_same_type05(self): #ct constraint errors
        self.login()

        orga01    = Organisation.objects.create(user=self.user, name='orga01')
        orga02    = Organisation.objects.create(user=self.user, name='orga02')
        contact01 = Contact.objects.create(user=self.user, first_name='John', last_name='Doe')
        contact02 = Contact.objects.create(user=self.user, first_name='Joe',  last_name='Gohn')

        rtype, sym_rtype = RelationType.create(('test-subject_foobar', 'manages',       [Contact]),
                                               ('test-object_foobar',  'is managed by', [Organisation])
                                              )

        post = self.client.post

        self.assertEqual(404, post('/creme_core/relation/add_from_predicate/save',
                                    data={
                                            'subject_id':   orga01.id,
                                            'predicate_id': rtype.id,
                                            'entities':     [orga02.id],
                                         }
                                  ).status_code
                        )
        self.assertEqual(0, Relation.objects.filter(type=rtype.id).count())

        self.assertEqual(404, post('/creme_core/relation/add_from_predicate/save',
                                    data={
                                            'subject_id':   contact01.id,
                                            'predicate_id': rtype.id,
                                            'entities':     [orga01.id, contact02.id],
                                         }
                                  ).status_code
                        )
        relations = Relation.objects.filter(type=rtype.id)
        self.assertEqual(1,         len(relations))
        self.assertEqual(orga01.id, relations[0].object_entity_id)

    def test_add_relations_with_same_type06(self): #property constraint errors
        self.login()

        subject_ptype = CremePropertyType.create(str_pk='test-prop_foobar01', text='Subject property')
        object_ptype  = CremePropertyType.create(str_pk='test-prop_foobar02', text='Contact property')

        bad_subject  = CremeEntity.objects.create(user=self.user)
        good_subject = CremeEntity.objects.create(user=self.user)
        bad_object   = CremeEntity.objects.create(user=self.user)
        good_object  = CremeEntity.objects.create(user=self.user)

        CremeProperty.objects.create(type=subject_ptype, creme_entity=good_subject)
        CremeProperty.objects.create(type=object_ptype, creme_entity=good_object)

        rtype, sym_rtype = RelationType.create(('test-subject_foobar', 'manages',       [], [subject_ptype]),
                                               ('test-object_foobar',  'is managed by', [], [object_ptype])
                                              )

        post = self.client.post

        self.assertEqual(404, post('/creme_core/relation/add_from_predicate/save',
                                    data={
                                            'subject_id':   bad_subject.id,
                                            'predicate_id': rtype.id,
                                            'entities':     [good_object.id],
                                         }
                                  ).status_code
                        )
        self.assertEqual(0, Relation.objects.filter(type=rtype.id).count())

        self.assertEqual(404, post('/creme_core/relation/add_from_predicate/save',
                                    data={
                                            'subject_id':   good_subject.id,
                                            'predicate_id': rtype.id,
                                            'entities':     [good_object.id, bad_object.id],
                                         }
                                  ).status_code
                        )
        relations = Relation.objects.filter(type=rtype.id)
        self.assertEqual(1,              len(relations))
        self.assertEqual(good_object.id, relations[0].object_entity_id)


    def test_relation_delete(self):
        self.login()

        subject_entity = CremeEntity.objects.create(user=self.user)
        object_entity  = CremeEntity.objects.create(user=self.user)

        rtype, sym_rtype = RelationType.create(('test-subject_foobar', 'is loving'), ('test-object_foobar',  'is loved by'))
        relation = Relation.objects.create(user=self.user, type=rtype, subject_entity=subject_entity, object_entity=object_entity)
        sym_relation = relation.symmetric_relation

        response = self.client.post('/creme_core/relation/delete', data={'id': relation.id})
        self.assertEqual(302, response.status_code)

        self.assertEqual(0, Relation.objects.filter(pk__in=[relation.pk, sym_relation.pk]).count())

    def test_relation_delete_similar(self):
        self.login()

        subject_entity01 = CremeEntity.objects.create(user=self.user)
        object_entity01  = CremeEntity.objects.create(user=self.user)

        subject_entity02 = CremeEntity.objects.create(user=self.user)
        object_entity02  = CremeEntity.objects.create(user=self.user)

        rtype01, useless = RelationType.create(('test-subject_love', 'is loving'), ('test-object_love', 'is loved by'))
        rtype02, useless = RelationType.create(('test-subject_son',  'is son of'), ('test-object_son',  'is parent of'))

        #will be deleted (normally)
        relation01 = Relation.objects.create(user=self.user, type=rtype01, subject_entity=subject_entity01, object_entity=object_entity01)
        relation02 = Relation.objects.create(user=self.user, type=rtype01, subject_entity=subject_entity01, object_entity=object_entity01)

        #won't be deleted (normally)
        relation03 = Relation.objects.create(user=self.user, type=rtype01, subject_entity=subject_entity01, object_entity=object_entity02) #different object
        relation04 = Relation.objects.create(user=self.user, type=rtype01, subject_entity=subject_entity02, object_entity=object_entity01) #different subject
        relation05 = Relation.objects.create(user=self.user, type=rtype02, subject_entity=subject_entity01, object_entity=object_entity01) #different type

        self.assertEqual(10, Relation.objects.count())

        response = self.client.post('/creme_core/relation/delete/similar',
                                    data={
                                            'subject_id': subject_entity01.id,
                                            'type':       rtype01.id,
                                            'object_id':  object_entity01.id,
                                         }
                                   )
        self.assertEqual(302, response.status_code)
        self.assertEqual(0,   Relation.objects.filter(pk__in=[relation01.pk, relation02.pk]).count())
        self.assertEqual(3,   Relation.objects.filter(pk__in=[relation03.pk, relation04.pk, relation05.pk]).count())

        #TODO: test other relation views...

