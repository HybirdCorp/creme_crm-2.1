# -*- coding: utf-8 -*-

################################################################################
#    Creme is a free/open-source Customer Relationship Management software
#    Copyright (C) 2009-2018  Hybird
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

from django.db.models.query_utils import Q
from django.utils.formats import number_format
from django.utils.html import escape, format_html, format_html_join


class FunctionFieldResult(object):
    __slots__ = ('_data',)

    def __init__(self, str_data):
        self._data = str_data

    def __unicode__(self, str_data):
        return self.for_html()

    def for_html(self):
        return escape(self._data)

    def for_csv(self):
        return self._data


class FunctionFieldDecimal(FunctionFieldResult):
    def _format_decimal(self):
        val = self._data
        # TODO: factorise with field_printers ?
        # TODO remove 'use_l10n' when settings.USE_L10N == True
        return number_format(val, use_l10n=True)  # TODO: ?? "if val is not None else ''"

    def for_html(self):
        return self._format_decimal()  # TODO: escape() ?

    def for_csv(self):
        return self._format_decimal()

# TODO: other types (date, datetime...)


class FunctionField(object):
    """A FunctionField is related to a model and represents a special method of
    this model : it has a verbose name and can be used by HeaderFilter to build
    a column (like regular fields).
    """
    name         = ''  # Name of the attr if the related model class
    verbose_name = ''  # Verbose name (used by HeaderFilter)
    has_filter   = False  # See EntityCell.has_a_filter
    is_hidden    = False  # See EntityCell.is_hidden
    choices      = None  # Choices for list_view filtering. Has to be like django choices (e.g: [(1, 'First choice', ...), ] )
    result_type  = FunctionFieldResult  # TODO: what about FunctionFieldResultsList([FunctionFieldDecimal(...), ...])
                                        #         ==> FunctionFieldResultsList or FunctionFieldDecimal ??

    @classmethod
    def filter_in_result(cls, search_string):
        return Q()

    # def __call__(self, entity):
    def __call__(self, entity, user):
        """"@return An instance of FunctionField object
        (so you can call for_html()/for_csv() on the result).
        """
        return self.result_type(getattr(entity, self.name)())

    @classmethod
    # def populate_entities(cls, entities):
    def populate_entities(cls, entities, user):
        """Optimisation used for list-views ; see HeaderFilter"""
        pass


class FunctionFieldResultsList(FunctionFieldResult):
    def __init__(self, iterable):
        self._data = list(iterable)

    def for_html(self):
        # return u'<ul>%s</ul>' % u''.join(u'<li>%s</li>' % e.for_html() for e in self._data)
        return format_html(u'<ul>{}</ul>',
                           format_html_join(
                               '', u'<li>{}</li>',
                               ([e.for_html()] for e in self._data)
                           )
                          )

    def for_csv(self):
        return u'/'.join(e.for_csv() for e in self._data)


class FunctionFieldsManager(object):
    def __init__(self, *function_fields):
        self._function_fields = {f_field.name: f_field for f_field in function_fields}
        self._parent = None

    def __iter__(self):
        manager = self

        while manager:
            for func_field in manager._function_fields.itervalues():
                yield func_field

            manager = manager._parent

    def add(self, *function_fields):
        self._function_fields.update((f_field.name, f_field) for f_field in function_fields)

    def get(self, name):
        func_field = self._function_fields.get(name)

        if not func_field and self._parent:
            func_field = self._parent.get(name)

        return func_field

    def new(self, *function_fields):
        """Use this method when you inherit a class, and you want to add new
        function fields to the inherited class, but not to the base class.
        """
        ffm = FunctionFieldsManager(*function_fields)
        ffm._parent = self

        return ffm
