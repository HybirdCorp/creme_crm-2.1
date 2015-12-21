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

from .base import Base

class Settings(Base):
    template_name = "activesync/commands/xml/settings/request_min.xml"
    command       = "Settings"

    def __init__(self, *args, **kwargs):
        super(Settings, self).__init__(*args, **kwargs)
        self._create_connection()

    def send(self, headers=None, *args, **kwargs):
        settings_headers = {}
        if headers:
            settings_headers.update(headers)

        xml = super(Settings, self).send({'get_user_infos': True, 'set_device_infos': False}, headers=headers)
        ns = "{Settings:}"

        self.smtp_address = None
        if xml is not None:
            # status =
            xml.find('%sStatus' % ns).text #TODO: not used ??
            self.smtp_address = xml.find('%(ns0)sUserInformation/%(ns0)sGet/%(ns0)sEmailAddresses/%(ns0)sSmtpAddress' % {'ns0': ns}).text
