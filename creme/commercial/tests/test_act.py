# -*- coding: utf-8 -*-

try:
    from datetime import date
    from functools import partial

    from django.contrib.contenttypes.models import ContentType
    from django.core.urlresolvers import reverse
    from django.utils.translation import ugettext as _

    from creme.creme_core.constants import PROP_IS_MANAGED_BY_CREME, DEFAULT_CURRENCY_PK
    from creme.creme_core.models import (RelationType, Relation, CremeProperty,
            EntityFilter, EntityFilterCondition)

    from creme.persons.tests.base import skipIfCustomContact, skipIfCustomOrganisation

    from creme.opportunities.models import SalesPhase  # Opportunity
    from creme.opportunities.tests import skipIfCustomOpportunity

    # from creme.activities.models import Activity
    from creme.activities.constants import REL_SUB_ACTIVITY_SUBJECT, ACTIVITYTYPE_MEETING
    from creme.activities.tests.base import skipIfCustomActivity

    from ..constants import REL_SUB_COMPLETE_GOAL
    from ..models import ActType, ActObjective, ActObjectivePatternComponent
    from .base import (CommercialBaseTestCase, skipIfCustomAct, skipIfCustomPattern,
            Contact, Organisation, Opportunity, Activity,
            Act, ActObjectivePattern)
except Exception as e:
    print('Error in <%s>: %s' % (__name__, e))


@skipIfCustomAct
class ActTestCase(CommercialBaseTestCase):
    @classmethod
    def setUpClass(cls):
        CommercialBaseTestCase.setUpClass()
        cls.populate('activities', 'opportunities', 'commercial')

        cls.ADD_URL = reverse('commercial__create_act')

    def _build_addobjective_url(self, act):
        return '/commercial/act/%s/add/objective' % act.id

    def _build_addobjectivefrompattern_url(self, act):
        return '/commercial/act/%s/add/objectives_from_pattern' % act.id

    def _build_create_related_entity_url(self, objective):
        return '/commercial/objective/%s/create_entity' % objective.id

    def _build_incr_url(self, objective):
        return '/commercial/objective/%s/incr' % objective.id

    def test_create(self):
        url = self.ADD_URL
        self.assertGET200(url)

        name = 'Act#1'
        atype = ActType.objects.create(title='Show')
        segment = self._create_segment()
        response = self.client.post(url, follow=True,
                                    data={'user':           self.user.pk,
                                          'name':           name,
                                          'expected_sales': 1000,
                                          'start':          '2011-11-20',
                                          'due_date':       '2011-12-25',
                                          'act_type':       atype.id,
                                          'segment':        segment.id,
                                         }
                                   )
        self.assertNoFormError(response)

        acts = Act.objects.all()
        self.assertEqual(1, len(acts))

        act = acts[0]
        self.assertEqual(name,  act.name)
        self.assertEqual(atype, act.act_type)
        self.assertEqual(date(year=2011, month=11, day=20), act.start)
        self.assertEqual(date(year=2011, month=12, day=25), act.due_date)

        self.assertRedirects(response, act.get_absolute_url())

    def test_create02(self):
        "Error: due date < start"
        atype = ActType.objects.create(title='Show')
        segment = self._create_segment()
        response = self.assertPOST200(self.ADD_URL, follow=True,
                                      data={'user':           self.user.pk,
                                            'name':           'Act#1',
                                            'expected_sales': 1000,
                                            'start':          '2011-11-20',
                                            'due_date':       '2011-09-25',
                                            'act_type':       atype.id,
                                            'segment':        segment.id,
                                           }
                                     )
        self.assertFormError(response, 'form', None, _(u"Due date can't be before start."))
        self.assertFalse(Act.objects.all())

    def test_create03(self):
        "Error: start/due date not filled"
        atype = ActType.objects.create(title='Show')
        segment = self._create_segment()

        def post(**kwargs):
            return self.assertPOST200(self.ADD_URL, follow=True,
                                    data=dict(user=self.user.pk,
                                              name='Act#1',
                                              expected_sales=1000,
                                              act_type=atype.id,
                                              segment=segment.id,
                                              **kwargs
                                             )
                                    )

        msg = _(u"This field is required.")
        self.assertFormError(post(start='2011-11-20'),    'form', 'due_date', msg)
        self.assertFormError(post(due_date='2011-11-20'), 'form', 'start',    msg)

    def create_act(self, name='NAME', expected_sales=1000):
        return Act.objects.create(user=self.user, name=name,
                                  expected_sales=expected_sales, cost=50,
                                  goal='GOAL', start=date(2010, 11, 25),
                                  due_date=date(2011, 12, 26),
                                  act_type=ActType.objects.create(title='Show'),
                                  segment=self._create_segment('Segment - %s' % name),
                                 )

    def test_edit(self):
        act = self.create_act()
        url = act.get_edit_absolute_url()
        self.assertGET200(url)

        name = 'Act#1'
        expected_sales = 2000
        cost = 100
        goal = 'Win'
        atype = ActType.objects.create(title='Demo')
        segment = self._create_segment('Segment#2')
        response = self.client.post(url, follow=True,
                                    data={'user':            self.user.pk,
                                          'name':            name,
                                          'start':           '2011-11-20',
                                          'due_date':        '2011-12-25',
                                          'expected_sales':  expected_sales,
                                          'cost':            cost,
                                          'goal':            goal,
                                          'act_type':        atype.id,
                                          'segment':         segment.id,
                                         }
                                   )
        self.assertNoFormError(response)
        self.assertRedirects(response, act.get_absolute_url())

        act = self.refresh(act)
        self.assertEqual(name,           act.name)
        self.assertEqual(cost,           act.cost)
        self.assertEqual(expected_sales, act.expected_sales)
        self.assertEqual(goal,           act.goal)
        self.assertEqual(atype,          act.act_type)
        self.assertEqual(date(year=2011, month=11, day=20), act.start)
        self.assertEqual(date(year=2011, month=12, day=25), act.due_date)

    def test_edit02(self):
        "Error: due_date < start date"
        act = self.create_act()

        atype = ActType.objects.create(title='Demo')
        segment = self._create_segment('Segment#2')
        response = self.assertPOST200(act.get_edit_absolute_url(), follow=True,
                                      data={'user':            self.user.pk,
                                            'name':            'Act#1',
                                            'start':           '2011-11-20',
                                            'due_date':        '2011-09-25',
                                            'expected_sales':  2000,
                                            'cost':            100,
                                            'goal':            'Win',
                                            'act_type':        atype.id,
                                            'segment':         segment.id,
                                           }
                                     )
        self.assertFormError(response, 'form', None, [_(u"Due date can't be before start.")])
        self.assertEqual(date(year=2011, month=12, day=26), self.refresh(act).due_date)

    def test_listview(self):
        create_act = partial(Act.objects.create, user=self.user, expected_sales=1000,
                             cost=50, goal='GOAL',
                             start=date(2010, 11, 25), due_date=date(2011, 12, 26),
                             act_type=ActType.objects.create(title='Show'),
                             segment=self._create_segment(),
                            )
        acts = [create_act(name='NAME_%s' % i) for i in xrange(1, 3)]

        response = self.assertGET200(Act.get_lv_absolute_url())

        with self.assertNoException():
            acts_page = response.context['entities']

        self.assertEqual(1, acts_page.number)
        self.assertEqual(2, acts_page.paginator.count)
        self.assertEqual(set(acts), set(acts_page.object_list))

    def test_detailview(self):
        act = self.create_act()
        self.assertGET200(act.get_absolute_url())

    @skipIfCustomOrganisation
    @skipIfCustomOpportunity
    def test_create_linked_opportunity(self):
        act = self.create_act()

        url = reverse('commercial__create_opportunity', args=(act.id,))
        self.assertGET200(url)

        user = self.user
        create_orga = partial(Organisation.objects.create, user=user)
        emitter = create_orga(name='Ferraille corp')
        target  = create_orga(name='World company')

        CremeProperty.objects.create(type_id=PROP_IS_MANAGED_BY_CREME, creme_entity=emitter)

        name  = 'Opportunity01'
        phase = SalesPhase.objects.all()[0]
        response = self.client.post(url,
                                    data={'user':        user.id,
                                          'name':        name,
                                          'sales_phase': phase.id,
                                          'target':      '{"ctype": {"id": "%s"}, "entity":"%s"}' % (
                                                                target.entity_type_id,
                                                                target.id
                                                            ),
                                          'emitter':     emitter.id,
                                          'currency':    DEFAULT_CURRENCY_PK,
                                         }
                                   )
        self.assertNoFormError(response)

        opp = self.get_object_or_fail(Opportunity, name=name)
        self.assertEqual(phase,   opp.sales_phase)
        self.assertEqual(target,  opp.target)
        self.assertEqual(emitter, opp.emitter)

        self.assertRelationCount(1, opp, REL_SUB_COMPLETE_GOAL, act)

    def test_add_objective01(self):
        act = self.create_act()
        url = self._build_addobjective_url(act)
        self.assertGET200(url)
        self.assertEqual(0, ActObjective.objects.count())

        name = 'Objective#1'
        counter_goal = 20
        response = self.client.post(url, data={'name':            name,
                                               'counter_goal':    counter_goal,
                                               'entity_counting': self._build_ctypefilter_field(),
                                              }
                                   )
        self.assertNoFormError(response)

        objectives = ActObjective.objects.filter(act=act)
        self.assertEqual(1, len(objectives))

        objective = objectives[0]
        self.assertEqual(name,         objective.name)
        self.assertEqual(act,          objective.act)
        self.assertEqual(0,            objective.counter)
        self.assertEqual(counter_goal, objective.counter_goal)
        self.assertIsNone(objective.ctype)
        self.assertIsNone(objective.filter)

        self.assertEqual(0, objective.get_count())
        self.assertFalse(objective.reached)

        objective.counter = counter_goal
        objective.save()
        objective = self.refresh(objective)  # Refresh cache
        self.assertEqual(counter_goal, objective.get_count())
        self.assertTrue(objective.reached)

    def test_add_objective02(self):
        "Count by content type only"
        act = self.create_act()

        name  = 'Objective#2'
        counter_goal = 2
        ct = ContentType.objects.get_for_model(Organisation)
        response = self.client.post(self._build_addobjective_url(act),
                                    data={'name':            name,
                                          'entity_counting': self._build_ctypefilter_field(ct),
                                          'counter_goal':    counter_goal,
                                         }
                                   )
        self.assertNoFormError(response)

        objective = self.get_object_or_fail(ActObjective, act=act, name=name)
        self.assertEqual(name,         objective.name)
        self.assertEqual(act,          objective.act)
        self.assertEqual(0,            objective.counter)
        self.assertEqual(counter_goal, objective.counter_goal)
        self.assertEqual(ct,           objective.ctype)
        self.assertIsNone(objective.filter)

    def test_add_objective03(self):
        "Count with EntityFilter"
        act = self.create_act()
        ct = ContentType.objects.get_for_model(Organisation)

        create_efilter = EntityFilter.create
        pub_efilter  = create_efilter('test-filter01', 'Acme', Organisation, is_custom=True)
        priv_efilter = create_efilter('test-filter_priv01', 'Acme', Organisation,
                                      is_custom=True, is_private=True, user=self.other_user,
                                     )

        name = 'Objective#3'
        counter_goal = 2

        def post(efilter):
            return self.client.post(self._build_addobjective_url(act),
                                    data={'name':            name,
                                          'entity_counting': self._build_ctypefilter_field(ct, efilter),
                                          'counter_goal':    counter_goal,
                                         }
                                   )

        response = post(priv_efilter)
        self.assertEqual(200, response.status_code)
        self.assertFormError(response, 'form', 'entity_counting',
                             _(u'This filter is invalid.')
                            )

        response = post(pub_efilter)
        self.assertNoFormError(response)

        objective = self.get_object_or_fail(ActObjective, act=act, name=name)
        self.assertEqual(0,            objective.counter)
        self.assertEqual(counter_goal, objective.counter_goal)
        self.assertEqual(ct,           objective.ctype)
        self.assertEqual(pub_efilter,  objective.filter)

    @skipIfCustomPattern
    def test_add_objectives_from_pattern01(self):
        "No component"
        act = self.create_act(expected_sales=21000)
        pattern = ActObjectivePattern.objects.create(user=self.user, name='Mr Pattern',
                                                     average_sales=5000,  # NB: 21000 / 5000 => Ratio = 5
                                                     segment=act.segment,
                                                    )

        url = self._build_addobjectivefrompattern_url(act)
        self.assertGET200(url)
        self.assertNoFormError(self.client.post(url, data={'pattern': pattern.id}))

        objectives = ActObjective.objects.filter(act=act)
        self.assertEqual(1, len(objectives))
        self.assertEqual(5, objectives[0].counter_goal)

    @skipIfCustomPattern
    def test_add_objectives_from_pattern02(self):
        "With components"
        act = self.create_act(expected_sales=20000)
        pattern = ActObjectivePattern.objects.create(user=self.user, name='Mr Pattern',
                                                     average_sales=5000,  # NB: 20000 / 5000 => Ratio = 4
                                                     segment=act.segment,
                                                    )

        get_ct = ContentType.objects.get_for_model
        ct_contact = get_ct(Contact)
        ct_orga    = get_ct(Organisation)

        efilter = EntityFilter.create('test-filter01', 'Ninja', Contact, is_custom=True)

        create_comp = partial(ActObjectivePatternComponent.objects.create, pattern=pattern)
        root01 = create_comp(name='Root01', success_rate=20, ctype=ct_contact, filter=efilter)
        create_comp(name='Root02',   success_rate=50)
        create_comp(name='Child 01', success_rate=33, parent=root01)
        create_comp(name='Child 02', success_rate=10, parent=root01, ctype=ct_orga)

        self.assertNoFormError(self.client.post(self._build_addobjectivefrompattern_url(act),
                                                data={'pattern': pattern.id},
                                               )
                              )
        self.assertEqual(5, ActObjective.objects.filter(act=act).count())

        with self.assertNoException():
            objectives  = act.objectives
            objective01 = objectives.get(name='Root01')
            objective02 = objectives.get(name='Root02')
            objective11 = objectives.get(name='Child 01')
            objective12 = objectives.get(name='Child 02')
            objective00 = objectives.exclude(pk__in=[objective01.id, objective02.id,
                                                     objective11.id, objective12.id,
                                                    ]
                                            )[0]

        self.assertTrue(all(o.counter == 0 
                                for o in [objective00, objective01, objective02,
                                          objective11, objective12,
                                         ]
                           )
                       )

        # Content types
        self.assertIsNone(objective00.ctype_id)
        self.assertEqual(ct_contact, objective01.ctype)
        self.assertEqual(ct_orga,    objective12.ctype)
        self.assertIsNone(objective02.ctype_id)
        self.assertIsNone(objective11.ctype_id)

        # Entity Filters
        self.assertIsNone(objective00.filter_id)
        self.assertEqual(efilter, objective01.filter)
        self.assertIsNone(objective12.filter_id)
        self.assertIsNone(objective02.filter_id)
        self.assertIsNone(objective11.filter_id)

        self.assertEqual(4,   objective00.counter_goal)  # ratio = 4
        self.assertEqual(20,  objective01.counter_goal)  # 20% -> 4  * 5
        self.assertEqual(8,   objective02.counter_goal)  # 50% -> 4  * 2
        self.assertEqual(61,  objective11.counter_goal)  # 33% -> 20 * 3,3
        self.assertEqual(200, objective12.counter_goal)  # 10% -> 20 * 10

    def test_edit_objective01(self):
        act = self.create_act()
        objective = ActObjective.objects.create(act=act, name='OBJ#1')
        self.assertEqual(1, objective.counter_goal)

        url = objective.get_edit_absolute_url()
        self.assertGET200(url)

        name = 'OBJ_NAME'
        efilter = EntityFilter.create('test-filter01', 'Acme', Organisation, is_custom=True)
        ct = efilter.entity_type
        counter_goal = 3
        response = self.client.post(url,
                                    data={'name':            name,
                                          'entity_counting': self._build_ctypefilter_field(ct, efilter),
                                          'counter_goal':    counter_goal,
                                         }
                                   )
        self.assertNoFormError(response)

        objective = self.refresh(objective)
        self.assertEqual(name,         objective.name)
        self.assertEqual(counter_goal, objective.counter_goal)
        self.assertEqual(ct,           objective.ctype)
        self.assertEqual(efilter,      objective.filter)

    def test_edit_objective02(self):
        "Private filter"
        priv_efilter = EntityFilter.create('test-filter_priv01', 'Acme (private)', Organisation,
                                           is_custom=True, is_private=True, user=self.other_user,
                                          )
        act = self.create_act()
        objective = ActObjective.objects.create(act=act, name='OBJ#1', counter_goal=3,
                                                ctype=priv_efilter.entity_type,
                                                filter=priv_efilter,
                                               )

        name = 'New name'
        pub_efilter = EntityFilter.create('test-filter01', 'Acme', Organisation, is_custom=True)
        counter_goal = 4
        response = self.client.post(objective.get_edit_absolute_url(),
                                    data={'name':            name,
                                          # Should not be used
                                          'entity_counting': self._build_ctypefilter_field(pub_efilter.entity_type,
                                                                                           pub_efilter,
                                                                                          ),
                                          'counter_goal':    counter_goal,
                                         }
                                   )
        self.assertNoFormError(response)

        objective = self.refresh(objective)
        self.assertEqual(name,         objective.name)
        self.assertEqual(counter_goal, objective.counter_goal)
        self.assertEqual(priv_efilter, objective.filter)  # <===

    def test_delete_objective(self):
        act = self.create_act()
        objective = ActObjective.objects.create(act=act, name='OBJ#1')
        ct = ContentType.objects.get_for_model(ActObjective)

        response = self.client.post('/creme_core/entity/delete_related/%s' % ct.id, 
                                    data={'id': objective.id}
                                   )
        self.assertRedirects(response, act.get_absolute_url())
        self.assertDoesNotExist(objective)

    def test_incr_objective_counter01(self):
        act = self.create_act()
        objective = ActObjective.objects.create(act=act, name='OBJ#1')
        self.assertEqual(0, objective.counter)

        url = self._build_incr_url(objective)
        self.assertPOST200(url, data={'diff': 1})
        self.assertEqual(1, self.refresh(objective).counter)

        self.assertPOST200(url, data={'diff': 2})
        self.assertEqual(3, self.refresh(objective).counter)

        self.assertPOST200(url, data={'diff': -3})
        self.assertEqual(0, self.refresh(objective).counter)

    def test_incr_objective_counter02(self):
        "Relationships counter -> error"
        act = self.create_act()
        objective = ActObjective.objects.create(act=act, name='Orga counter', counter_goal=2,
                                                ctype=ContentType.objects.get_for_model(Organisation),
                                               )
        self.assertPOST409(self._build_incr_url(objective), data={'diff': 1})

    def test_objective_create_entity01(self):
        "Alright (No filter, quick form exists, credentials are OK)"
        act = self.create_act()
        objective = ActObjective.objects.create(act=act, name='Orga counter', counter_goal=2,
                                                ctype=ContentType.objects.get_for_model(Organisation),
                                               )

        url = self._build_create_related_entity_url(objective)
        self.assertGET200(url)

        name = 'Nerv'
        response = self.assertPOST200(url,
                                      data={'user': self.user.id,
                                            'name': name,
                                           }
                                     )
        self.assertNoFormError(response)

        nerv = self.get_object_or_fail(Organisation, name=name)
        self.assertRelationCount(1, nerv, REL_SUB_COMPLETE_GOAL, act)

    def test_objective_create_entity02(self):
        "Not a relationships counter objective"
        act = self.create_act()
        objective = ActObjective.objects.create(act=act, name='OBJ#1')
        self.assertGET409(self._build_create_related_entity_url(objective))

    def test_objective_create_entity03(self):
        "No quick for this entity type"
        act = self.create_act()
        objective = ActObjective.objects.create(act=act, name='Act counter', counter_goal=2,
                                                ctype=ContentType.objects.get_for_model(Act),
                                               )
        self.assertGET409(self._build_create_related_entity_url(objective))

    def test_objective_create_entity04(self):
        "The objective has a filter -> error"
        act = self.create_act()

        efilter = EntityFilter.create('test-filter01', 'Acme', Organisation, is_custom=True,
                                      conditions=[EntityFilterCondition.build_4_field(
                                                        model=Organisation,
                                                        operator=EntityFilterCondition.ICONTAINS,
                                                        name='name', values=['Ferraille'],
                                                    )
                                                 ],
                                     )

        objective = ActObjective.objects.create(act=act, name='Orga counter', counter_goal=2,
                                                ctype=ContentType.objects.get_for_model(Organisation),
                                                filter=efilter,
                                               )
        self.assertGET409(self._build_create_related_entity_url(objective))

    @skipIfCustomContact
    @skipIfCustomOrganisation
    def test_count_relations01(self):
        user = self.user
        rtype = self.get_object_or_fail(RelationType, pk=REL_SUB_COMPLETE_GOAL)

        act = self.create_act()
        objective = ActObjective.objects.create(act=act, name='Orga counter', counter_goal=2,
                                                ctype=ContentType.objects.get_for_model(Organisation)
                                               )
        self.assertEqual(0, objective.get_count())
        self.assertFalse(objective.reached)

        completes_goal = partial(Relation.objects.create, type=rtype, object_entity=act, user=user)
        create_orga    = partial(Organisation.objects.create, user=user)

        completes_goal(subject_entity=create_orga(name='Ferraille corp'))
        objective = self.refresh(objective)  # Refresh cache
        self.assertEqual(1, objective.get_count())
        self.assertFalse(objective.reached)

        orga02 = create_orga(name='World company')
        completes_goal(subject_entity=orga02)
        objective = self.refresh(objective)  # Refresh cache
        self.assertEqual(2, objective.get_count())
        self.assertTrue(objective.reached)

        contact = Contact.objects.create(user=user, first_name='Monsieur', last_name='Ferraille')
        completes_goal(subject_entity=contact)
        objective = self.refresh(objective)  # Refresh cache
        self.assertEqual(2, objective.get_count())
        self.assertTrue(objective.reached)

        orga02.trash()
        self.assertEqual(1, self.refresh(objective).get_count())

    @skipIfCustomContact
    @skipIfCustomOrganisation
    def test_count_relations02(self):
        "With filter"
        user = self.user

        efilter = EntityFilter.create('test-filter01', 'Acme', Organisation, is_custom=True,
                                      conditions=[EntityFilterCondition.build_4_field(
                                                        model=Organisation,
                                                        operator=EntityFilterCondition.ICONTAINS,
                                                        name='name', values=['Ferraille'],
                                                    ),
                                                 ],
                                     )

        act = self.create_act()
        objective = ActObjective.objects.create(act=act, name='Orga counter', counter_goal=2,
                                                ctype=ContentType.objects.get_for_model(Organisation),
                                                filter=efilter,
                                               )
        self.assertEqual(0, objective.get_count())

        create_orga  = partial(Organisation.objects.create, user=user)
        orga01 = create_orga(name='Ferraille corp')
        orga02 = create_orga(name='World company')
        orga03 = create_orga(name='Ferraille inc')

        all_orgas = set(efilter.filter(Organisation.objects.all()))
        self.assertIn(orga01, all_orgas)
        self.assertNotIn(orga02, all_orgas)

        completes_goal = partial(Relation.objects.create, type_id=REL_SUB_COMPLETE_GOAL,
                                 object_entity=act, user=user
                                )
        completes_goal(subject_entity=orga01)
        self.assertEqual(1, self.refresh(objective).get_count())

        completes_goal(subject_entity=orga02)
        self.assertEqual(1, self.refresh(objective).get_count())

        completes_goal(subject_entity=orga03)
        self.assertEqual(2, self.refresh(objective).get_count())

        contact = Contact.objects.create(user=user, first_name='Monsieur', last_name='Ferraille')
        completes_goal(subject_entity=contact)
        self.assertEqual(2, self.refresh(objective).get_count())

    def assertObjectivesEqual(self, obj_a, obj_b):
        self.assertEqual(obj_a.name,         obj_b.name)
        self.assertEqual(obj_a.counter,      obj_b.counter)
        self.assertEqual(obj_a.counter_goal, obj_b.counter_goal)
        self.assertEqual(obj_a.ctype,        obj_b.ctype)

    def test_clone(self):
        act = self.create_act()

        efilter = EntityFilter.create('test-filter01', 'Acme', Organisation, is_custom=True)

        create_obj = partial(ActObjective.objects.create, act=act) 
        obj1 = create_obj(name='Hello counter')
        obj2 = create_obj(name='Orga counter', counter_goal=2, filter=efilter,
                          ctype=ContentType.objects.get_for_model(Organisation),
                         )

        cloned = act.clone()
        self.assertEqual(act.name,     cloned.name)
        self.assertEqual(act.due_date, cloned.due_date)
        self.assertEqual(act.segment,  cloned.segment)

        cloned_objs = ActObjective.objects.filter(act=cloned).order_by('name')
        self.assertEqual(2, len(cloned_objs))

        self.assertObjectivesEqual(obj1, cloned_objs[0])
        self.assertObjectivesEqual(obj2, cloned_objs[1])

    @skipIfCustomOrganisation
    @skipIfCustomOpportunity
    def test_related_opportunities(self):
        rtype = self.get_object_or_fail(RelationType, pk=REL_SUB_COMPLETE_GOAL)

        user = self.user

        act = self.create_act()
        self.assertEqual([], act.get_related_opportunities())
        self.assertEqual(0,  act.get_made_sales())

        sales_phase = SalesPhase.objects.create(name='Foresale')

        create_orga = partial(Organisation.objects.create, user=user)
        emitter = create_orga(name='Ferraille corp')
        target = create_orga(name='World company')

        create_opp = partial(Opportunity.objects.create, user=user, sales_phase=sales_phase,
                             emitter=emitter, target=target,
                            )
        create_rel = partial(Relation.objects.create, type=rtype, object_entity=act, user=user)
        opp01 = create_opp(name='OPP01', closing_date=date.today(), estimated_sales=2000)
        create_rel(subject_entity=opp01)

        act = self.refresh(act)  # Refresh cache
        self.assertEqual([opp01], list(act.get_related_opportunities()))
        self.assertEqual(0,       act.get_made_sales())

        opp01.made_sales = 1500; opp01.save()
        self.assertEqual(1500, self.refresh(act).get_made_sales())
        self.assertEqual(2000, self.refresh(act).get_estimated_sales())

        opp02 = create_opp(name='OPP02', closing_date=date.today(), made_sales=500, estimated_sales=3000)
        create_rel(subject_entity=opp02)

        act  = self.refresh(act) #refresh cache
        opps = act.get_related_opportunities()
        self.assertEqual(2, len(opps))
        self.assertEqual({opp01, opp02}, set(opps))
        self.assertEqual(2000, self.refresh(act).get_made_sales())
        self.assertEqual(5000, self.refresh(act).get_estimated_sales())

        opp01.trash()
        self.assertEqual([opp02], self.refresh(act).get_related_opportunities())

    def test_delete_type(self):
        act = self.create_act()
        atype = act.act_type

        self.assertPOST404('/creme_config/commercial/act_type/delete', data={'id': atype.pk})
        self.get_object_or_fail(ActType, pk=atype.pk)

        act = self.get_object_or_fail(Act, pk=act.pk)
        self.assertEqual(atype, act.act_type)

    @skipIfCustomOrganisation
    @skipIfCustomActivity
    @skipIfCustomOpportunity
    def test_link_to_activity(self):
        user = self.user
        act1 = self.create_act('Act#1')
        act2 = self.create_act('Act#2')

        create_orga = partial(Organisation.objects.create, user=user)
        opp = Opportunity.objects.create(user=user, name='Opp01',
                                         sales_phase=SalesPhase.objects.create(name='Foresale'),
                                         closing_date=date.today(),
                                         emitter=create_orga(name='Ferraille corp'),
                                         target=create_orga(name='World company'),
                                        )

        create_rel = partial(Relation.objects.create, subject_entity=opp, user=user)
        create_rel(type_id=REL_SUB_COMPLETE_GOAL, object_entity=act1)
        create_rel(type_id=REL_SUB_COMPLETE_GOAL, object_entity=act2)

        create_dt = self.create_datetime
        meeting = Activity.objects.create(user=user, title='Meeting #01', type_id=ACTIVITYTYPE_MEETING,
                                          start=create_dt(year=2011, month=5, day=20, hour=14, minute=0),
                                          end=create_dt(year=2011,   month=6, day=1,  hour=15, minute=0),
                                         )

        create_rel(type_id=REL_SUB_ACTIVITY_SUBJECT, object_entity=meeting)
        self.assertRelationCount(1, meeting, REL_SUB_COMPLETE_GOAL, act1)
        self.assertRelationCount(1, meeting, REL_SUB_COMPLETE_GOAL, act2)
