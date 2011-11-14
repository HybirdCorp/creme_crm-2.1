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

try:
    from os.path import join, dirname, abspath

    from activesync.commands.airsync import AirSync
    from activesync.tests.commands.base import BaseASTestCase
except Exception as e:
    print 'Error:', e


#TODO: tests!!
class AirSyncASTestCase(BaseASTestCase):
    def setUp(self):
        super(AirSyncASTestCase, self).setUp()
        self.test_files_path = join(dirname(abspath(__file__)), '..', 'data', 'commands', 'airsync')
        self.test_files = []
        self.test_files_paths = [join(self.test_files_path, f) for f in self.test_files]

#    def test_airsync01(self):
#        as_ = AirSync(*self.params)
#        as_.send(headers={'test_files': ";".join(self.test_files_paths) })
