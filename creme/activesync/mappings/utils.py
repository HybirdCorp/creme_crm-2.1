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

from datetime import datetime
from xml.sax.saxutils import escape
import warnings

from django.db import models

# from creme.creme_core.utils.dates import get_dt_to_iso8601_str
# from creme.creme_core.utils.meta import get_instance_field_info

from ..models import EntityASData


# NB: old creme_core.utils.meta.get_instance_field_info
def get_instance_field_info(obj, field_name):
    """ For a field_name 'att1__att2__att3', it searches and returns the tuple
    (class of obj.att1.att2.get_field('att3'), obj.att1.att2.att3)
    @return : (field_class, field_value)
    """
    warnings.warn("get_instance_field_info() function is deprecated ; "
                  "use creme_core.utils.meta.FieldInfo.value_from() instead.",
                  DeprecationWarning
                 )

    subfield_names = field_name.split('__')

    try:
        for subfield_name in subfield_names[:-1]:
            obj = getattr(obj, subfield_name)  # Can be None if a M2M has no related value

        subfield_name = subfield_names[-1]
        field = obj._meta.get_field(subfield_name)
        field_value = getattr(obj, subfield_name)

        if field.many_to_many:
            field_value = field_value.all()

        return field.__class__, field_value
    except (AttributeError, models.FieldDoesNotExist):
        return None, ''


# NB: old creme_core.utils.dates.get_dt_to_iso8601_str()
# XXX: it is not true ISO 8601 !!!!
def get_dt_to_iso8601_str(dt):
    """Converts the datetime into a string in iso8601 format without any separator.
    >>> get_dt_to_iso8601_str(datetime.datetime(2011, 4, 27, 10, 9, 54))
    '20110427T100954Z'
    """
    # warnings.warn("get_dt_to_iso8601_str() method is deprecated.", DeprecationWarning)

    return dt.strftime('%Y%m%dT%H%M%SZ')


# NB: old creme_core.utils.dates.get_dt_from_iso8601_str()
# XXX: rename, it is not true ISO 8601 !!!!
def get_dt_from_iso8601_str(dt_str):
    """Builds a datetime instance from a iso8601 (without any separators) formatted string.
    @throws ValueError
    >>> get_dt_from_iso8601_str("20110427T100954Z")
    datetime.datetime(2011, 4, 27, 10, 9, 54)
    """
    # warnings.warn("get_dt_from_iso8601_str() method is deprecated.", DeprecationWarning)

    return datetime.strptime(dt_str, '%Y%m%dT%H%M%SZ')


def _format_value_for_AS(field_class, field_value):
    if field_class is not None:
        if issubclass(field_class, models.BooleanField):
            return 1 if field_value else 0

        if issubclass(field_class, models.DateField):
            if field_value:
                field_value = datetime(*field_value.timetuple()[:6])
                field_class = models.DateTimeField

        if issubclass(field_class, (models.DateTimeField, models.DateField)):
            if field_value:
                return get_dt_to_iso8601_str(field_value)

            return None

    return field_value


def serialize_entity(entity, mapping):
    """Serialize an entity in xml respecting namespaces prefixes
       TODO/NB: Need to send an empty value when the entity hasn't a value ?
       TODO: Add the possibility to subset entity fields ?
    """
    from creme.activesync.mappings import CREME_AS_MAPPING#TODO: Remove the cyclic import
    xml = []
    xml_append = xml.append

    reverse_ns = {v: "A%s" % i for i, v in enumerate(mapping.keys())}
    namespaces = reverse_ns

    pre_serialization = CREME_AS_MAPPING[entity.__class__]['pre_serialization']

    for ns, values in mapping.iteritems():
        prefix = namespaces.get(ns)
        for c_field, xml_field in values.iteritems():
            value   = None
            f_class = None

            if callable(c_field):
                value = c_field(entity)
            else:
                f_class, value = get_instance_field_info(entity, c_field)

            value = _format_value_for_AS(f_class, value)

            if value in (None, ''):
                try:
                    value = EntityASData.objects.get(entity=entity, field_name=xml_field).field_value
                except EntityASData.DoesNotExist:
                    pass

            value = pre_serialization(value, c_field, xml_field, f_class, entity)


            if value:
                try:
                    value = escape(value)
                except Exception:
                    pass
                xml_append("<%(prefix)s%(tag)s>%(value)s</%(prefix)s%(tag)s>" %
                           {
                            'prefix': '%s:' % prefix if prefix else '',
                            'tag': xml_field,
                            'value': value,  # Problems with unicode
                            }
                           )
    return "".join(xml)
