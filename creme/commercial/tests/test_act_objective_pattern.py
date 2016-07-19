# -*- coding: utf-8 -*-

try:
    from functools import partial

    from django.contrib.contenttypes.models import ContentType
    from django.core.urlresolvers import reverse
    from django.utils.translation import ugettext as _

    from creme.creme_core.tests.fake_models import (FakeContact as Contact,
            FakeOrganisation as Organisation)
    from creme.creme_core.models import EntityFilter

    from ..models import ActObjectivePatternComponent
    from .base import CommercialBaseTestCase, skipIfCustomPattern, ActObjectivePattern
except Exception as e:
    print('Error in <%s>: %s' % (__name__, e))


@skipIfCustomPattern
class ActObjectivePatternTestCase(CommercialBaseTestCase):
    # @classmethod
    # def setUpClass(cls):
    #     CommercialBaseTestCase.setUpClass()
    #     cls.populate('commercial')

    def _build_addcomp_url(self, pattern):
        return '/commercial/objective_pattern/%s/add_component' % pattern.id

    def _build_parent_url(self, component):
        return '/commercial/objective_pattern/component/%s/add_parent' % component.id

    def test_create(self):
        url = reverse('commercial__create_pattern')
        self.assertGET200(url)

        segment = self._create_segment()
        name = 'ObjPattern#1'
        average_sales = 5000
        response = self.client.post(url, follow=True,
                                    data={'user':          self.user.pk,
                                          'name':          name,
                                          'average_sales': average_sales,
                                          'segment':       segment.id,
                                         }
                                   )
        self.assertNoFormError(response)

        patterns = ActObjectivePattern.objects.all()
        self.assertEqual(1, len(patterns))

        pattern = patterns[0]
        self.assertEqual(name,          pattern.name)
        self.assertEqual(average_sales, pattern.average_sales)
        self.assertEqual(segment,       pattern.segment)

        self.assertRedirects(response, pattern.get_absolute_url())

    def _create_pattern(self, name='ObjPattern', average_sales=1000):
        return ActObjectivePattern.objects.create(user=self.user, name=name,
                                                  average_sales=average_sales,
                                                  segment=self._create_segment(),
                                                 )

    def test_edit(self):
        name = 'ObjPattern'
        average_sales = 1000
        pattern = self._create_pattern(name, average_sales)

        url = pattern.get_edit_absolute_url()
        self.assertGET200(url)

        name += '_edited'
        average_sales *= 2
        segment = self._create_segment('Segment#2')
        response = self.client.post(url, follow=True,
                                    data={'user':          self.user.pk,
                                          'name':          name,
                                          'average_sales': average_sales,
                                          'segment':       segment.id,
                                         }
                                   )
        self.assertNoFormError(response)

        pattern = self.refresh(pattern)
        self.assertEqual(name,          pattern.name)
        self.assertEqual(average_sales, pattern.average_sales)
        self.assertEqual(segment,       pattern.segment)

    def test_listview(self):
        create_patterns = partial(ActObjectivePattern.objects.create, user=self.user)
        patterns = [create_patterns(name='ObjPattern#%s' % i,
                                    average_sales=1000 * i,
                                    segment=self._create_segment('Segment #%s' % i),
                                   ) for i in xrange(1, 4)
                   ]

        response = self.assertGET200(ActObjectivePattern.get_lv_absolute_url())

        with self.assertNoException():
            patterns_page = response.context['entities']

        self.assertEqual(1, patterns_page.number)
        self.assertEqual(3, patterns_page.paginator.count)
        self.assertEqual(set(patterns), set(patterns_page.object_list))

    def test_add_root_pattern_component01(self):
        "No parent component, no counted relation"
        pattern  = self._create_pattern()

        url = self._build_addcomp_url(pattern)
        self.assertGET200(url)

        name = 'Signed opportunities'
        response = self.client.post(url, data={'name':            name,
                                               'success_rate':    10,
                                               'entity_counting': self._build_ctypefilter_field(),
                                              }
                                   )
        self.assertNoFormError(response)

        components = pattern.components.all()
        self.assertEqual(1, len(components))

        component = components[0]
        self.assertEqual(name, component.name)
        self.assertIsNone(component.parent)
        self.assertIsNone(component.ctype)

    def test_add_root_pattern_component02(self):
        "Counted relation (no parent component)"
        pattern = self._create_pattern()
        name = 'Called contacts'
        ct = ContentType.objects.get_for_model(Contact)
        response = self.client.post(self._build_addcomp_url(pattern),
                                    data={'name':            name,
                                          'entity_counting': self._build_ctypefilter_field(ct),
                                          'success_rate':    15,
                                         }
                                   )
        self.assertNoFormError(response)

        components = pattern.components.all()
        self.assertEqual(1, len(components))

        component = components[0]
        self.assertEqual(name, component.name)
        self.assertEqual(ct,   component.ctype)
        self.assertIsNone(component.filter)

    def test_add_root_pattern_component03(self):
        "Counted relation with filter (no parent component)"
        pattern = self._create_pattern()
        name = 'Called contacts'
        ct = ContentType.objects.get_for_model(Contact)
        efilter = EntityFilter.create('test-filter01', 'Ninja', Contact, is_custom=True)
        response = self.client.post(self._build_addcomp_url(pattern),
                                    data={'name':            name,
                                          'entity_counting': self._build_ctypefilter_field(ct, efilter),
                                          'success_rate':    15,
                                         }
                                   )
        self.assertNoFormError(response)

        with self.assertNoException():
            component = pattern.components.get(name=name)

        self.assertEqual(ct,      component.ctype)
        self.assertEqual(efilter, component.filter)

    def test_add_child_pattern_component01(self):
        "Parent component"
        pattern = self._create_pattern()
        comp01 = ActObjectivePatternComponent.objects.create(name='Signed opportunities',
                                                             pattern=pattern, success_rate=50
                                                            )

        url = '/commercial/objective_pattern/component/%s/add_child' % comp01.id
        self.assertGET200(url)

        name = 'Spread Vcards'
        self.assertNoFormError(self.client.post(url, data={'name':            name,
                                                           'success_rate':    20,
                                                           'entity_counting': self._build_ctypefilter_field(),
                                                          }
                                               )
                              )

        children = comp01.children.all()
        self.assertEqual(1, len(children))

        comp02 = children[0]
        self.assertEqual(name,   comp02.name)
        self.assertEqual(comp01, comp02.parent)
        self.assertIsNone(comp02.ctype)

        name = 'Called contacts'
        ct   = ContentType.objects.get_for_model(Contact)
        response = self.client.post(url, data={'name':            name,
                                               'entity_counting': self._build_ctypefilter_field(ct),
                                               'success_rate':    60,
                                              }
                                   )
        self.assertNoFormError(response)
        self.assertEqual(2, comp01.children.count())

        with self.assertNoException():
            comp03 = comp01.children.get(name=name)

        self.assertEqual(ct, comp03.ctype)

    def test_add_parent_pattern_component01(self):
        pattern = self._create_pattern()
        comp01 = ActObjectivePatternComponent.objects.create(name='Sent mails',
                                                             pattern=pattern,
                                                             success_rate=5,
                                                            )

        url = self._build_parent_url(comp01)
        self.assertGET200(url)

        name = 'Signed opportunities'
        success_rate = 50
        self.assertNoFormError(self.client.post(url, data={'name':           name,
                                                          'success_rate':    success_rate,
                                                          'entity_counting': self._build_ctypefilter_field(),
                                                          }
                                               )
                              )

        pattern = self.refresh(pattern)
        components = pattern.components.order_by('id')
        self.assertEqual(2, len(components))

        child = components[0]
        self.assertEqual(comp01, child)

        parent = components[1]
        self.assertEqual(name,         parent.name)
        self.assertEqual(success_rate, parent.success_rate)
        self.assertIsNone(parent.parent)
        self.assertEqual(child.parent, parent)

    def test_add_parent_pattern_component02(self):
        pattern = self._create_pattern()

        create_comp = partial(ActObjectivePatternComponent.objects.create, pattern=pattern)
        comp01 = create_comp(name='Signed opportunities', success_rate=50)
        comp02 = create_comp(name='Spread Vcards',        success_rate=1, parent=comp01)

        name = 'Called contacts'
        ct   = ContentType.objects.get_for_model(Contact)
        response = self.client.post(self._build_parent_url(comp02),
                                    data={'name':            name,
                                          'entity_counting': self._build_ctypefilter_field(ct),
                                          'success_rate':    20,
                                         }
                                   )
        self.assertNoFormError(response)

        pattern = self.get_object_or_fail(ActObjectivePattern, pk=pattern.id)
        components = pattern.components.order_by('id')
        self.assertEqual(3, len(components))

        grandpa = components[0]
        self.assertEqual(comp01, grandpa)

        child = components[1]
        self.assertEqual(comp02, child)

        parent = components[2]
        self.assertEqual(name, parent.name)
        self.assertEqual(ct,   parent.ctype)

        self.assertEqual(child.parent,  parent)
        self.assertEqual(parent.parent, grandpa)

    def test_add_pattern_component_errors(self):
        pattern = self._create_pattern()
        url = self._build_addcomp_url(pattern)

        response = self.client.post(url, data={'name':         'Signed opportunities',
                                               'success_rate': 0,  # Minimunm is 1
                                              }
                                   )
        self.assertFormError(response, 'form', 'success_rate',
                             _(u'Ensure this value is greater than or equal to %(limit_value)s.') % {
                                    'limit_value': 1,
                                }
                            )

        response = self.client.post(url, data={'name':         'Signed opportunities',
                                               'success_rate': 101,  # Maximum is 100
                                              }
                                   )
        self.assertFormError(response, 'form', 'success_rate',
                             _(u'Ensure this value is less than or equal to %(limit_value)s.') % {
                                    'limit_value': 100,
                                }
                            )

    def test_get_component_tree(self):
        pattern = self._create_pattern()

        create_comp = partial(ActObjectivePatternComponent.objects.create,
                              pattern=pattern, success_rate=1,
                             )
        root01  = create_comp(name='Root01')
        root02  = create_comp(name='Root02')
        child01 = create_comp(name='Child 01', parent=root01)
        child11 = create_comp(name='Child 11', parent=child01)
        child12 = create_comp(name='Child 12', parent=child01)
        child13 = create_comp(name='Child 13', parent=child01)
        child02 = create_comp(name='Child 02', parent=root01)
        child21 = create_comp(name='Child 21', parent=child02)

        comptree = pattern.get_components_tree()  # TODO: test that no additional queries are done ???
        self.assertIsInstance(comptree, list)
        self.assertEqual(2, len(comptree))

        rootcomp01 = comptree[0]
        self.assertIsInstance(rootcomp01, ActObjectivePatternComponent)
        self.assertEqual(root01, rootcomp01)
        self.assertEqual(root02, comptree[1])

        children = rootcomp01.get_children()
        self.assertEqual(2, len(children))

        compchild01 = children[0]
        self.assertIsInstance(compchild01, ActObjectivePatternComponent)
        self.assertEqual(child01, compchild01)
        self.assertEqual(3, len(compchild01.get_children()))

        self.assertEqual(1, len(children[1].get_children()))

    def _delete_comp(self, comp):
        ct = ContentType.objects.get_for_model(ActObjectivePatternComponent)

        return self.client.post('/creme_core/entity/delete_related/%s' % ct.id,
                                data={'id': comp.id}
                               )

    def test_delete_pattern_component01(self):
        pattern = self._create_pattern()
        comp01 = ActObjectivePatternComponent.objects.create(name='Signed opportunities',
                                                             pattern=pattern, success_rate=20
                                                            )

        self.assertNoFormError(self._delete_comp(comp01), status=302)
        self.assertDoesNotExist(comp01)

    def test_delete_pattern_component02(self):
        pattern = self._create_pattern()
        create_comp = partial(ActObjectivePatternComponent.objects.create, pattern=pattern, success_rate=1)
        comp00 = create_comp(name='Signed opportunities')  # NB: should not be removed
        comp01 = create_comp(name='DELETE ME')
        comp02 = create_comp(name='Will be orphaned01',  parent=comp01)
        comp03 = create_comp(name='Will be orphaned02',  parent=comp01)
        comp04 = create_comp(name='Will be orphaned03',  parent=comp02)
        comp05 = create_comp(name='Smiles done')  # NB: should not be removed
        comp06 = create_comp(name='Stand by me',         parent=comp05)  # NB: should not be removed

        self.assertNoFormError(self._delete_comp(comp01), status=302)

        remaining_ids = pattern.components.values_list('id', flat=True)
        self.assertEqual(3, len(remaining_ids))
        self.assertEqual({comp00.id, comp05.id, comp06.id}, set(remaining_ids))

    def assertCompNamesEqual(self, comp_qs, *names):
        self.assertEqual(set(names), set(comp_qs.values_list('name', flat=True)))

    def test_actobjectivepattern_clone01(self):
        pattern = self._create_pattern()

        ct_contact = ContentType.objects.get_for_model(Contact)
        ct_orga    = ContentType.objects.get_for_model(Organisation)
        efilter = EntityFilter.create('test-filter01', 'Ninja', Contact, is_custom=True)

        create_comp = partial(ActObjectivePatternComponent.objects.create,
                              pattern=pattern, success_rate=1,
                             )
        comp1   = create_comp(name='1',                    ctype=ct_orga)
        comp11  = create_comp(name='1.1',   parent=comp1,  success_rate=20, ctype=ct_contact)
        comp111 = create_comp(name='1.1.1', parent=comp11)
        comp112 = create_comp(name='1.1.2', parent=comp11)
        comp12  = create_comp(name='1.2',   parent=comp1,  ctype=ct_contact, filter=efilter)
        comp121 = create_comp(name='1.2.1', parent=comp12)
        comp122 = create_comp(name='1.2.2', parent=comp12)
        comp2   = create_comp(name='2',                    success_rate=50)
        comp21  = create_comp(name='2.1',   parent=comp2)
        comp211 = create_comp(name='2.1.1', parent=comp21)
        comp212 = create_comp(name='2.1.2', parent=comp21)
        comp22  = create_comp(name='2.2',   parent=comp2)
        comp221 = create_comp(name='2.2.1', parent=comp22)
        comp222 = create_comp(name='2.2.2', parent=comp22)

        cloned_pattern = pattern.clone()

        filter_comp = partial(ActObjectivePatternComponent.objects.filter, pattern=cloned_pattern)
        self.assertEqual(14, filter_comp().count())

        cloned_comp1 = self.get_object_or_fail(ActObjectivePatternComponent,
                                               pattern=cloned_pattern, name=comp1.name,
                                              )
        self.assertIsNone(cloned_comp1.parent)
        self.assertEqual(1, cloned_comp1.success_rate)
        self.assertEqual(ct_orga, cloned_comp1.ctype)
        self.assertIsNone(cloned_comp1.filter)

        with self.assertNoException():
            cloned_comp11, cloned_comp12 = cloned_comp1.children.all()

        self.assertEqual(ct_contact, cloned_comp11.ctype)
        self.assertEqual(efilter,    cloned_comp12.filter)

        self.assertCompNamesEqual(filter_comp(parent__name__in=['1.1', '1.2']),
                                  '1.1.1', '1.1.2', '1.2.1', '1.2.2'
                                 )

        cloned_comp2 = self.get_object_or_fail(ActObjectivePatternComponent,
                                               pattern=cloned_pattern, name=comp2.name,
                                              )
        self.assertIsNone(cloned_comp2.parent)
        self.assertEqual(50, cloned_comp2.success_rate)
        self.assertIsNone(cloned_comp2.ctype)
        self.assertIsNone(cloned_comp1.filter)
        self.assertCompNamesEqual(cloned_comp2.children, '2.1', '2.2')

        self.assertCompNamesEqual(filter_comp(parent__name__in=['2.1', '2.2']),
                                  '2.1.1', '2.1.2', '2.2.1', '2.2.2'
                                 )

    def test_inneredit(self):
        pattern = self._create_pattern()
        comp01 = ActObjectivePatternComponent.objects.create(name='signed opportunities',
                                                             pattern=pattern,
                                                             success_rate=50,
                                                            )

        build_url = self.build_inneredit_url
        url =  build_url(comp01, 'name')
        self.assertGET200(url)

        name = comp01.name.title()
        response = self.client.post(url, data={'entities_lbl': [unicode(comp01)],
                                               'field_value':  name,
                                              }
                                   )
        self.assertNoFormError(response)
        self.assertEqual(name, self.refresh(comp01).name)

        self.assertGET(400, build_url(comp01, 'success_rate'))
