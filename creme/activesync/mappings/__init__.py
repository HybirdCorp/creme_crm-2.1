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

from creme.activities import get_activity_model
#from creme.activities.models import Activity

from creme.persons import get_contact_model
#from creme.persons.models import Contact

from ..constants import SYNC_FOLDER_TYPE_CONTACT, SYNC_FOLDER_TYPE_APPOINTMENT, SYNC_FOLDER_TYPE_TASK
from .contact import CREME_CONTACT_MAPPING, save_contact, update_contact, serialize_contact, pre_serialize_contact
from .activity import CREME_MEETING_MAPPING, save_meeting, update_meeting, pre_serialize_meeting
from .utils import serialize_entity


Contact = get_contact_model()
Activity = get_activity_model()

#Mapping between AS folder types and creme types
FOLDERS_TYPES_CREME_TYPES_MAPPING = {
    SYNC_FOLDER_TYPE_CONTACT: Contact,
    SYNC_FOLDER_TYPE_APPOINTMENT: Activity,
    SYNC_FOLDER_TYPE_TASK: Activity,
}

CREME_TYPES_FOLDERS_TYPES_MAPPING = {v: k for k, v in FOLDERS_TYPES_CREME_TYPES_MAPPING.items()}

##Mapping between Creme types and AS Classes
#AS_CLASSES = {
#    Contact: "Contacts",
#    Task: "Tasks",
##    :"Email",
#    Meeting: "Calendar",
##    :"SMS",
#}

CREME_AS_MAPPING = {
    Contact:{
        'mapping': CREME_CONTACT_MAPPING,
        'class': "Contacts",
        'save': save_contact,
        'update': update_contact,
#        'serializer': serialize_contact,
        'serializer': serialize_entity,
        'type': SYNC_FOLDER_TYPE_CONTACT,
        'pre_serialization': pre_serialize_contact,
    },
    Activity:{
        'mapping': CREME_MEETING_MAPPING,
        'class': "Calendar",
        'save': save_meeting,
        'update': update_meeting,
        'serializer': serialize_entity,
        'type': SYNC_FOLDER_TYPE_APPOINTMENT,
        'pre_serialization': pre_serialize_meeting,#Method called before each field serialization
    }
}