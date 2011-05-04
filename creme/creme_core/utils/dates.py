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
import pytz

from datetime import datetime

from django.conf import settings

creme_tz = pytz.timezone(settings.TIME_ZONE)
utc_tz   = pytz.utc

def get_utc_dt_from_creme_dt(dt):
    if (dt.tzinfo is None) or (dt.tzinfo.utcoffset(dt) is None):
        dt = creme_tz.localize(dt)
    return dt.astimezone(utc_tz)

def get_creme_dt_from_utc_dt(dt):
    if (dt.tzinfo is None) or (dt.tzinfo.utcoffset(dt) is None):
        dt = utc_tz.localize(dt)
    return dt.astimezone(creme_tz)

def get_utc_now():
    return utc_tz.localize(datetime.utcnow())

def get_dt_to_iso8601_str(dt):
    """Returns the datetime to a string in iso8601 format without any separators
        >>> get_dt_to_iso8601_str(datetime.datetime(2011, 4, 27, 10, 9, 54))
        '20110427T100954Z'
    """
    return dt.strftime("%Y%m%dT%H%M%SZ")

def get_dt_from_iso8601_str(dt_str):
    """
        Returns an iso8601 formatted string without any separators from a datetime
        >>>get_dt_from_iso8601_str("20110427T100954Z")
        datetime.datetime(2011, 4, 27, 10, 9, 54)
    """
    return datetime.strptime(dt_str, "%Y%m%dT%H%M%SZ")

def get_naive_dt_from_tzdate(dt):
    """Needed (among others) for db saves, in particular MySQL which doesn't support timezone-aware datetimes"""
    return datetime(*dt.timetuple()[:6])