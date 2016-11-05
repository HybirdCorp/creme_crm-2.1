# -*- coding: utf-8 -*-

try:
    from django.db.models.query import QuerySet
    from django.utils.translation import ugettext as _

    from ..fake_models import FakeContact as Contact
    from .base import FieldTestCase
    from creme.creme_core.forms.widgets import DynamicSelect, UnorderedMultipleChoiceWidget
except Exception as e:
    print('Error in <%s>: %s' % (__name__, e))


class DynamicSelectTestCase(FieldTestCase):
    def test_options_list(self):
        select = DynamicSelect(options=[(1, 'A'), (2, 'B')])

        self.assertIsInstance(select.options, list)
        self.assertListEqual([(1, 'A'), (2, 'B')], select.choices)

    def test_options_queryset(self):
        user = self.login()
        Contact.objects.create(last_name='Doe', first_name='John', user=user)

        select = DynamicSelect(options=Contact.objects.values_list('id', 'last_name'))
        self.assertIsInstance(select.options, QuerySet)
        self.assertListEqual(list(Contact.objects.values_list('id', 'last_name')),
                             list(select.choices)
                            )

    def test_options_function(self):
        select = DynamicSelect(options=lambda: [(id, str(id)) for id in xrange(10)])

        self.assertTrue(callable(select.options))
        self.assertListEqual([(id_, str(id_)) for id_ in xrange(10)],
                             select.choices)

        self.assertListEqual([(id_, str(id_)) for id_ in xrange(10)],
                             select.choices)

    def test_options_generator(self):
        select = DynamicSelect(options=((id_, str(id_)) for id_ in xrange(10)))

        self.assertIsInstance(select.options, list)
        self.assertListEqual([(id_, str(id_)) for id_ in xrange(10)],
                             select.choices)

        self.assertListEqual([(id_, str(id_)) for id_ in xrange(10)],
                             select.choices)

    def test_render_options(self):
        select = DynamicSelect()
        self.assertEqual(u'<option value="%s">%s</option>' % (1, 'A'),
                         select.render_option([], 1, 'A'))

        self.assertEqual(u'<option value="%s" selected="selected">%s</option>' % (1, 'A'),
                         select.render_option(['1'], '1', 'A'))

    def test_render_options_choices(self):
        render_option = DynamicSelect().render_option
        Choice = DynamicSelect.Choice

        self.assertEqual(u'<option value="%s" disabled help="%s">%s</option>' % (1, 'is disabled', 'A'),
                         render_option(['2'], Choice(1, True, 'is disabled'), 'A')
                        )

        self.assertEqual(u'<option value="%s" disabled selected="selected" help="%s">%s</option>' % (
                                1, 'is disabled', 'A',
                            ),
                         render_option(['1'], Choice(1, True, 'is disabled'), 'A')
                        )

        self.assertEqual(u'<option value="%s" selected="selected" help="%s">%s</option>' % (
                                2, 'is enabled', 'B',
                            ),
                         render_option(['2'], Choice(2, False, 'is enabled'), 'B')
                        )

    def test_render(self):
        select = DynamicSelect(options=[(1, 'A'), (2, 'B')])
        self.assertHTMLEqual('<select class="ui-creme-input ui-creme-widget widget-auto ui-creme-dselect" '
                                     'name="test" url="" widget="ui-creme-dselect">'
                               '<option value="1">A</option>'
                               '<option value="2" selected="selected">B</option>'
                             '</select>',
                             select.render('test', 2)
                            )

        Choice = DynamicSelect.Choice
        select = DynamicSelect(options=[(Choice(1, True, 'disabled'), 'A'),
                                        (Choice(2, False, 'item B'), 'B'),
                                        (Choice(3, False, 'item C'), 'C'),
                                       ],
                              )
        self.assertHTMLEqual('<select class="ui-creme-input ui-creme-widget widget-auto ui-creme-dselect" '
                                     'name="test" url="" widget="ui-creme-dselect">'
                               '<option value="1" disabled help="disabled">A</option>'
                               '<option value="2" selected="selected" help="item B">B</option>'
                               '<option value="3" help="item C">C</option>'
                             '</select>',
                             select.render('test', 2)
                            )


class UnorderedMultipleChoiceTestCase(FieldTestCase):
    def test_option_list(self):
        select = UnorderedMultipleChoiceWidget(choices=[(1, 'A'), (2, 'B')])
        self.assertEqual(2, select._choice_count())

        self.assertEqual(u'<option value="%s">%s</option>' % (1, 'A'),
                         select.render_option([], 1, 'A')
                        )

        self.assertEqual(u'<option value="%s" selected="selected">%s</option>' % (1, 'A'),
                         select.render_option(['1'], '1', 'A')
                        )

        html = '''<div class="ui-creme-widget widget-auto ui-creme-checklistselect"
style="" widget="ui-creme-checklistselect">
  <select multiple="multiple" class="ui-creme-input" name="A">
    <option value="1">A</option>
    <option value="2" selected="selected">B</option>
    <option value="1">A</option>
    <option value="2" selected="selected">B</option>
  </select>
  <span class="checklist-counter"></span>
  <div class="checklist-body"><ul class="checklist-content  "></ul></div>
</div>'''
        self.assertHTMLEqual(html, select.render('A', (2,), choices=select.choices))

    def test_option_group_list(self):
        select = UnorderedMultipleChoiceWidget(choices=[('Group A', ((1, 'A'), (2, 'B'))),
                                                        ('Group B', ((3, 'C'), (4, 'D'), (5, 'E'))),
                                                       ],
                                              )
        self.assertEqual(5, select._choice_count())

        html = u'''<div class="ui-creme-widget widget-auto ui-creme-checklistselect"
style="" widget="ui-creme-checklistselect" >
  <select multiple="multiple" class="ui-creme-input" name="A">
    <optgroup label="Group A">
      <option value="1">A</option>
      <option value="2">B</option>
    </optgroup>
    <optgroup label="Group B">
      <option value="3" selected="selected">C</option>
      <option value="4" selected="selected">D</option>
      <option value="5">E</option>
    </optgroup>
    <optgroup label="Group A">
      <option value="1">A</option>
      <option value="2">B</option>
    </optgroup>
    <optgroup label="Group B">
      <option value="3" selected="selected">C</option>
      <option value="4" selected="selected">D</option>
      <option value="5">E</option>
    </optgroup>
  </select>
  <span class="checklist-counter"></span>
  <div class="checklist-header">
    <a type="button" class="checklist-check-all">%(check_all)s</a> | <a type="button" class="checklist-check-none">%(check_none)s</a>
  </div>
  <div class="checklist-body"><ul class="checklist-content  "></ul></div>
</div>''' % {
            'check_all':  _(u'Check all'),
            'check_none': _(u'Check none'),
        }
        self.assertHTMLEqual(html, select.render('A', (3, 4,), choices=select.choices))

    def test_render_options_choices(self):
        select = UnorderedMultipleChoiceWidget()
        Choice = UnorderedMultipleChoiceWidget.Choice
        self.assertEqual(u'<option value="%s" disabled help="%s">%s</option>' % (
                                1, 'is disabled', 'A',
                            ),
                         select.render_option(['2'], Choice(1, True, 'is disabled'), 'A')
                        )
        self.assertEqual(u'<option value="%s" disabled selected="selected" help="%s">%s</option>' % (
                                1, 'is disabled', 'A',
                            ),
                         select.render_option(['1'], Choice(1, True, 'is disabled'), 'A')
                        )
        self.assertEqual(u'<option value="%s" selected="selected" help="%s">%s</option>' % (
                                2, 'is enabled', 'B',
                            ),
                         select.render_option(['2'], Choice(2, False, 'is enabled'), 'B')
                        )
