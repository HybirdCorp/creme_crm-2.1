# -*- coding: utf-8 -*-

################################################################################
#    Creme is a free/open-source Customer Relationship Management software
#    Copyright (C) 2009-2010  Hybird
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

from django.conf import settings

from .utils.imports import safe_import_object


class NotRegistered(Exception):
    pass


class CremeApp(object):
    __slots__ = ('name', 'verbose_name', 'url')

    def __init__(self, name, verbose_name, url):
        self.name = name
        self.verbose_name = verbose_name
        self.url = url


class CremeRegistry(object):
    """Registry for Creme Applications and Entities."""

    def __init__(self):
        self._entity_models = []
        self._apps = {}
        self._generic_registry = {}

    def register_app(self, name, verbose_name, url=None):
        self._apps[name] = CremeApp(name, verbose_name, url)

    def get_app(self, name):
        app = self._apps.get(name)

        if app is None:
            raise NotRegistered("%s.get_app(): No app registered with this name: %s" % (self.__class__, name))

        return app

    def iter_apps(self):
        return self._apps.itervalues()

    def register_entity_models(self, *models):
        """Register CremeEntity models."""
        self._entity_models.extend(models)

    def iter_entity_models(self):
        return iter(self._entity_models)

    def register(self, key, value):
        """A generic registry map"""
        self._generic_registry[key] = value

    def get(self, key):
        value = self._generic_registry.get(key)

        if value is None:
            raise NotRegistered("Nothing registered with this key: %s" % (key,))

        return value

creme_registry = CremeRegistry()


class _BackendRegistry(object):
    def __init__(self, settings):
        self._backends = None
        self._settings = settings

    def _get_backends(self):
        if self._backends is None:
            backends = {}
            for backend in self._settings:
                BackendClass = safe_import_object(backend)
                if BackendClass is None:  # safe_import_object logged and Exception
                    continue

                backend_id = getattr(BackendClass, 'id', None)
                if backend_id is None:
                    raise Exception('Backend: %s has invalid id.' % BackendClass)

                if backend_id in backends:
                    raise Exception('Id: %s already used for %s. Please specify another id for %s' %
                                    (backend_id, backends[backend_id], BackendClass))

                backends[backend_id] = BackendClass
            self._backends = backends
        return self._backends

    def iterbackends(self):
        return self._get_backends().itervalues()

    def iterkeys(self):
        return self._get_backends().iterkeys()

    def get_backend(self, backend_id):
        return self._get_backends().get(backend_id)

import_backend_registry = _BackendRegistry(settings.IMPORT_BACKENDS)
export_backend_registry = _BackendRegistry(settings.EXPORT_BACKENDS)
