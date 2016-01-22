# -*- coding: utf-8 -*-

################################################################################
#    Creme is a free/open-source Customer Relationship Management software
#    Copyright (C) 2009-2011  Hybird
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

# See  middleware.global_info.GlobalInfoMiddleware

from collections import defaultdict

try:
    from threading import currentThread
except ImportError:
    from dummy_threading import currentThread


_globals = defaultdict(dict)


def get_global_info(key):
    thread_globals = _globals.get(currentThread())
    return thread_globals and thread_globals.get(key)


def set_global_info(**kwargs):
    _globals[currentThread()].update(kwargs)


def clear_global_info():
    # Don't use del _globals[currentThread()], it causes problems with dev server.
    _globals.pop(currentThread(), None)
