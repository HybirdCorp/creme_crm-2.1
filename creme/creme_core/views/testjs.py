# -*- coding: utf-8 -*-

################################################################################
#    Creme is a free/open-source Customer Relationship Management software
#    Copyright (C) 2009-2015  Hybird
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
################################################################################

from datetime import date #datetime
from time import sleep

import logging
from os import listdir
from os.path import join
from random import randint
from re import compile as re_compile

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.utils.safestring import mark_safe
from django.utils.timezone import now

from ..auth.decorators import login_required
from ..core.exceptions import ConflictError
from ..global_info import set_global_info
from ..gui import block_registry
from ..gui.block import PaginatedBlock
from ..gui.field_printers import (print_image, print_urlfield, print_datetime,
        print_date, print_duration, print_foreignkey, print_many2many)
from ..utils import is_testenvironment
from ..utils.media import get_current_theme, creme_media_themed_url as media_url

from creme.persons.models.contact import Contact


logger = logging.getLogger(__name__)


TEST_TEMPLATE_PATH = join(settings.CREME_ROOT, 'creme_core', 'templates', 'creme_core', 'tests')
TEST_TEMPLATE_BLOCK_PATH = join(TEST_TEMPLATE_PATH, 'blocks')
TEST_IMAGE_URLS = ('images/add_32.png',
                   'images/404.png',
                   'images/500.png',
                   'images/action_48.png',
                   'images/action_not_in_time_48.png',
                   'images/wait.gif',
                  )

class MockImage(object):
    def __init__(self, url, width, height=None):
        self.url = url
        self.width = width
        self.height = height or width

    def html(self, entity):
        return mark_safe(print_image(entity, self, entity.user, None))


class MockManyToMany(object):
    def __init__(self, model):
        self.model = model

    def all(self):
        return self.model.objects.all()

    def filter(self, **kwargs):
        return self.model.objects.filter(**kwargs)


class Dummy(object):
    def __init__(self, id, user):
        self.user = user
        self.name = u'Dummy (%d)' % id
        self.image = MockImage(media_url(TEST_IMAGE_URLS[randint(0, len(TEST_IMAGE_URLS) - 1)]), randint(16, 64)).html(self)
        self.url = mark_safe(print_urlfield(self, media_url('images/add_16.png'), self.user, None))
        self.datetime = mark_safe(print_datetime(self, now(), user, None))
        self.date = mark_safe(print_date(self, date.today(), user, None))
        self.duration = mark_safe(print_duration(self, '%d:%d:%d' % (randint(0, 23), randint(0, 59), randint(0, 59)), user, None))
        self.foreignkey = mark_safe(print_foreignkey(self, Contact.objects.filter(is_user=True)[0], user, None))
        self.manytomany = mark_safe(print_many2many(self, MockManyToMany(Contact), user, None))

    def __unicode__(self):
        return self.name


class DummyListBlock(PaginatedBlock):
    id_           = PaginatedBlock.generate_id('creme_core', 'test_dummy_list')
    verbose_name  = u'Dummies'
    dependencies  = ()
    permission    = 'creme_config.can_admin'
    template_name = join(TEST_TEMPLATE_BLOCK_PATH, 'block_dummy_list.html')
    data          = None
    configurable  = False

    def detailview_display(self, context):
        request = context['request']
        user = request.user
        refresh = request.GET.get('refresh', False)

        min_count = request.GET.get('min', '0')
        min_count = int(min_count) if min_count.isdigit() else 0

        if refresh or self.data is None:
            self.data = [Dummy(id, user) for id in xrange(max(min_count, randint(0, 100)))]

        context['min_block_count'] = min_count

        return self._render(self.get_block_template_context(context, self.data,
                                                            update_url='/creme_core/blocks/reload/basic/%s/' % self.id_
                                                           )
                           )

dummy_list_block = DummyListBlock()

def js_testview_or_404(request, message, error):
    if is_testenvironment(request) or not settings.FORCE_JS_TESTVIEW:
        raise Http404(error)

    logger.warn(message)

def js_testview_context(request, viewname):
    try:
        block_registry[dummy_list_block.id_]
    except:
        logger.info('Register dummy object list block %s' % dummy_list_block.id_)
        block_registry.register(dummy_list_block)

    test_view_pattern = re_compile('^test_(?P<name>[\d\w]+)\.html$')
    test_views = []

    for filename in listdir(TEST_TEMPLATE_PATH):
        matches = test_view_pattern.match(filename)
        name = matches.group('name') if matches is not None else None

        if name:
            test_views.append((name, name.capitalize()))

    get = request.GET.get

    return  {
        'THEME_LIST':      [(theme_id, unicode(theme_vname))
                                for theme_id, theme_vname in settings.THEMES
                           ],
        'THEME_NAME':      get('theme', get_current_theme()),
        'TEST_VIEW_LIST':  test_views,
        'TEST_VIEW':       viewname,
        'TEST_SCREEN':     get('screen', ''),
        'TEST_HEADLESS':     get('headless', False),
        'TEST_CONTENTTYPES': dict(ContentType.objects.values_list('model', 'id'))
    }

def test_http_response(request):
    if not is_testenvironment(request) and not settings.FORCE_JS_TESTVIEW:
        raise Http404('This is view is only reachable during javascript or server unittests')

    logger.warn("Beware : If you are not running unittest this view shouldn't be reachable. Check your server configuration.")

    status = int(request.GET.get('status', 200))
    delay = int(request.GET.get('delay', 0))

    if delay > 0:
        sleep(delay / 1000.0)

    if status == 403:
        raise PermissionDenied('Operation is not allowed')

    if status == 404:
        raise Http404('No such result or unknown url')

    if status == 409:
        raise ConflictError('Conflicting operation')

    if status == 500:
        raise Exception('Server internal error')

    if request.is_ajax():
        return HttpResponse('XML Http Response %d' % status,
                            content_type='text/javascript', status=status,
                           )

    return HttpResponse('<p>Http Response %d</p>' % status,
                        content_type='text/html', status=status,
                       )

@login_required
def test_js(request):
    js_testview_or_404(request, 
                       "Beware : If you are not running unittest this view shouldn't be reachable. Check your server configuration.",
                       'This is view is only reachable during javascript unittests')

    return render(request, 'creme_core/test_js.html')

@login_required
def test_widget(request, widget):
    js_testview_or_404(request, 
                       "Beware : If you are not in testing javascript widgets this view shouldn't be reachable. Check your server configuration.",
                       'This is view is only reachable during javascript debug')

    context = js_testview_context(request, widget)
    theme = context['THEME_NAME']
    usertheme = get_current_theme()

    set_global_info(usertheme=theme)

    try:
        if widget:
            return render(request, 'creme_core/tests/test_' + widget + '.html', context)

        return render(request, 'creme_core/tests/test.html', context)
    finally:
        set_global_info(usertheme=usertheme)
