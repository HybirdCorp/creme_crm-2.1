# -*- coding: utf-8 -*-

################################################################################
#    Creme is a free/open-source Customer Relationship Management software
#    Copyright (C) 2009-2016  Hybird
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

from restkit import Resource, BasicAuth, set_logging

from django.conf import settings


#set_logging("debug")
set_logging("error")
#set_logging("info")

class Connection(Resource):
    # def __init__(self,  url, pool_instance=None, **kwargs):
    def __init__(self,  url, **kwargs):
        super(Connection, self).__init__(url, follow_redirect=True,
                                         max_follow_redirect=10,
                                         # pool_instance=pool_instance,
                                         timeout=settings.CONNECTION_TIMEOUT,
                                         **kwargs
                                       )

    def post(self, path=None, payload=None, headers=None, cmd="", device_id=None, device_type="SmartPhone", **params):
        min_headers = {
#            "MS-ASProtocolVersions": "1.0,2.0,2.5,12.0",
            "MS-ASProtocolVersions": "2.5",
            "Ms-Asprotocolversion": "2.5",
#            "Ms-Asprotocolversion": "12.0",
#            "Ms-Asprotocolversion": "14.0",
            "User-Agent": "CremeCRM/1.0",
            "Connection": "close",
            "Content-Type": "application/vnd.ms-sync.wbxml",
#            "Authorization: Basic %s" % base64.encode(username+':'+password),#Not used here, but can be another auth method
        }

        if headers:
            min_headers.update(headers)

        return super(Connection, self).post(path=path, payload=payload, headers=min_headers,
                                            Cmd=cmd, DeviceId=device_id, DeviceType=device_type,
                                            **params
                                           )

    @staticmethod
    def create(url, user, pwd, *args, **kwargs):
        filters = [BasicAuth(user, pwd)]
        try:
            _filters = kwargs.pop('filters')
            filters.extend(_filters)
        except KeyError:
            pass
        return Connection(url, filters=filters, *args, **kwargs)

    def send(self, cmd, content, device_id, *args, **kwargs):
        return self.post(cmd=cmd, payload=content, device_id=device_id, *args, **kwargs).body_string()
