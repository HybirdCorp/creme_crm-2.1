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

import base64
import datetime
import os
from random import randint
import time

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.files.base import ContentFile
from django.db import models
from django.utils import formats
from django.utils.translation import ugettext as _

from creme.creme_core.models import Relation, RelationType
from creme.creme_core.utils.meta import get_instance_field_info
from creme.creme_core.views.file_handling import handle_uploaded_file, MAXINT

# from creme.media_managers.models import Image
from creme.documents import get_document_model, get_folder_model
from creme.documents.utils import get_image_format

from creme.persons import get_organisation_model, get_contact_model, get_address_model
from creme.persons.models import Position, Civility #Organisation, Contact
from creme.persons.constants import REL_SUB_EMPLOYED_BY

from ..utils import get_b64encoded_img_of_max_weight

Document = get_document_model()
Folder = get_folder_model()

Organisation = get_organisation_model()
Contact = get_contact_model()
Address = get_address_model()


def get_encoded_contact_img(contact=None, needs_attr=False, *args, **kwargs):
    if needs_attr:
        return 'image'

    encoded_img = None
#    if contact and contact.image is not None:
    if contact:
        if contact.image is not None:
            image_path = str(contact.image.image.file)
            file_size = os.path.getsize(image_path)
            if file_size > settings.PICTURE_LIMIT_SIZE:
                encoded_img = get_b64encoded_img_of_max_weight(image_path, settings.PICTURE_LIMIT_SIZE)
            else:
                encoded_img = contact.image.get_encoded(encoding="base64")
        else:
            encoded_img = ""

    return encoded_img

def get_repr(contact=None, needs_attr=False, *args, **kwargs):
    if needs_attr:
        return ''
    return unicode(contact)

def get_organisation(contact=None, needs_attr=False, *args, **kwargs):
    if needs_attr:
        return 'organisation'

    organisation = ""
    relations = Relation.objects.filter(subject_entity=contact, type=REL_SUB_EMPLOYED_BY)

    if relations:
        organisation = unicode(relations[0].object_entity.get_real_entity())

    return organisation

CREME_CONTACT_MAPPING = {
    'Contacts:': {
        'civility__title'         : 'Title',
        'first_name'              : 'FirstName',
        'last_name'               : 'LastName',
        'skype'                   : 'Home2PhoneNumber',
        'phone'                   : 'HomePhoneNumber',
        'mobile'                  : 'MobilePhoneNumber',
        'position__title'         : 'JobTitle',
#        'sector__sector_name'     : None,
        'email'                   : 'Email1Address',
        'url_site'                : 'WebPage',
        'billing_address__city'   : 'BusinessCity',
        'billing_address__state'  : 'BusinessState',
        'billing_address__country': 'BusinessCountry',
        'billing_address__po_box' : 'BusinessPostalCode',
        'billing_address__address': 'BusinessStreet',
        'shipping_address__city'   : 'OtherCity',
        'shipping_address__state'  : 'OtherState',
        'shipping_address__country': 'OtherCountry',
        'shipping_address__po_box' : 'OtherPostalCode',
        'shipping_address__address': 'OtherStreet',
        'birthday'                : 'Birthday',
        get_encoded_contact_img   : 'Picture',#'image'
        get_organisation          : 'CompanyName',
        get_repr                  : 'FileAs',
    },
    'AirSyncBase:': {
#        'description': 'Body',#Not implemented in z-push
    },
#    'Contacts2:':
#    {
##        'id': 'CustomerId',#Not really usefull
#    }
}

if not settings.IS_ZPUSH:
    CREME_CONTACT_MAPPING['AirSyncBase:'].update({'description': 'Body'})

### Contact helpers
def create_or_update_organisation(contact, d, user, history=None):
    organisation = d.pop('organisation', None)

    if organisation is not None:
        try: #TODO: Organisation.objects.get_or_create
            org = Organisation.objects.get(name__iexact=organisation, user=user)
        except Organisation.DoesNotExist:
            org = Organisation.objects.create(name=organisation, user=user)
            if history is not None:
                history.changes = [(_(u"Contact's organisation created"), org)]
        except Organisation.MultipleObjectsReturned:
            org = Organisation.objects.filter(name__iexact=organisation, user=user)[0]

        Relation.objects.get_or_create(subject_entity=contact,
                                       type=RelationType.objects.get(pk=REL_SUB_EMPLOYED_BY),
                                       object_entity=org,
                                       user=user,
                                      )

def create_or_update_address(contact, prefix, data, history=None):
    pop = data.pop
    address = getattr(contact, '%s_address' % prefix)#if exception happens means model change

    city            = pop('%s_address__city'    % prefix, None)
    state           = pop('%s_address__state'   % prefix, None)
    country         = pop('%s_address__country' % prefix, None)
    po_box          = pop('%s_address__po_box'  % prefix, None)
    address_content = pop('%s_address__address' % prefix, None)

    changes = []

    if address is not None:
        if city:
            address.city = city
            changes.append(('%s_address__city' % prefix, city))

        if state:
            address.state = state
            changes.append(('%s_address__state' % prefix, state))

        if country:
            address.country = country
            changes.append(('%s_address__country' % prefix, country))

        if po_box:
            address.po_box = po_box
            changes.append(('%s_address__po_box'  % prefix, po_box))

        if address_content:
            address.address = address_content
            changes.append(('%s_address__address' % prefix, address_content))

        address.save()
    elif any([city, state, country, po_box, address_content]): #TODO: use Address.__nonzero__()
        c_address = Address(city=city,
                            state=state,
                            country=country,
                            po_box=po_box,
                            address=address_content,
                           )

        #TODO: "c_address.onwer = contact"
        c_address.content_type = ContentType.objects.get_for_model(Contact)
        c_address.object_id = contact.id
        c_address.save()
        setattr(contact, '%s_address' % prefix, c_address)
        changes.append(('%s_address' % prefix, c_address))

    if history is not None:
        history.changes = changes

def create_or_update_civility(contact, d, history=None):
    civility_title = d.pop('civility__title', None)
    if civility_title is not None:
        old_civility = contact.civility
        contact.civility = Civility.objects.get_or_create(title=civility_title)[0]

        if history is not None and contact.civility != old_civility:
            history.changes = [('civility__title', contact.civility)]

def create_or_update_position(contact, d, history=None):
    position_title = d.pop('position__title', None)
    if position_title is not None:
        old_position = contact.position
        contact.position = Position.objects.get_or_create(title=position_title)[0]

        if history is not None and contact.position != old_position:
            history.changes = [('position__title', contact.position)]

def create_image_from_b64(contact, d, user):
    image_b64 = d.pop('image', None)
    if image_b64 is not None:
        contact_has_img = contact.image is not None

        if image_b64 == "":
            if contact_has_img:
                contact.image.delete()
            return

        if contact_has_img:
            img_entity = contact.image
            img_entity.image.delete()  # Deleting the old file
        else:
            # img_entity = Image()
            img_entity = Document()

        image_data = base64.decodestring(image_b64)
        image_format = get_image_format(image_data)
        # img_entity.image = handle_uploaded_file(ContentFile(base64.decodestring(image_b64)), path=['upload','images'], name='file_%08x.%s' % (randint(0, MAXINT), image_format))
        img_entity.image = handle_uploaded_file(ContentFile(image_data),
                                                path=['upload', 'documents'],
                                                name='file_%08x.%s' % (randint(0, MAXINT), image_format),
                                               )
        img_entity.folder = Folder.objects.get_or_create(title=_('Images'),
                                                         parent_folder=None,
                                                         defaults={'user': user},
                                                        )[0]
        img_entity.description = _('Imported by activesync')
        img_entity.user = user
        img_entity.save()
        contact.image = img_entity
###
def _format_data(model_or_entity, data):
    for field_name, value in data.iteritems():
        field_class, field_value = get_instance_field_info(model_or_entity, field_name)
        if field_class is not None and issubclass(field_class, (models.DateTimeField, models.DateField)):
            datetime_formatted = False
            for format in formats.get_format('DATETIME_INPUT_FORMATS'):
                try:
                    data[field_name] = datetime.datetime(*time.strptime(value, format)[:6])
                    datetime_formatted = True
                except ValueError:
                    continue

            if not datetime_formatted:
                data[field_name] = None
        elif isinstance(value, basestring):
            data[field_name] = value
#            data[field_name] = value.decode('utf-8')

def save_contact(data, user, *args, **kwargs):
    """Save a contact from a populated data dict
        @Returns : A saved contact instance
    """
    c = Contact()
    ct_contact = ContentType.objects.get_for_model(Contact)
    pop = data.pop

    pop('', None)

    create_or_update_civility(c, data)
    create_or_update_position(c, data)

    #TODO:Use create_or_update_address
    b_address = Address(city=pop('billing_address__city', None),
                        state=pop('billing_address__state', None),
                        country=pop('billing_address__country', None),
                        po_box=pop('billing_address__po_box', None),
                        address=pop('billing_address__address', None),
                       )
    c.billing_address  = b_address

    #TODO:Use create_or_update_address
    s_address = Address(city=pop('shipping_address__city', None),
                        state=pop('shipping_address__state', None),
                        country=pop('shipping_address__country', None),
                        po_box=pop('shipping_address__po_box', None),
                        address=pop('shipping_address__address', None),
                       )
    c.shipping_address = s_address

    create_image_from_b64(c, data, user)

    c.user = user

    _format_data(c, data)

    c.__dict__.update(data) #TODO: setattr() ??
    c.save() #TODO: are the addresses OK (when they do not have a PK yet) ??

    create_or_update_organisation(c, data, user)

    #TODO: "b_address.owner = c" instead
    b_address.content_type = ct_contact
    b_address.object_id = c.id
    b_address.save()

    #TODO: idem
    s_address.content_type = ct_contact
    s_address.object_id = c.id
    s_address.save()

    return c

def update_contact(contact, data, user, history, *args, **kwargs):
    """Update a contact instance from a updated data dict
    @Returns : A saved contact instance
    """
    #pop_ = data.pop
    #pop_('', None)
    data.pop('', None)

    create_or_update_civility(contact, data, history)
    create_or_update_position(contact, data, history)

    create_or_update_address(contact, 'billing',  data, history)
    create_or_update_address(contact, 'shipping', data, history)

    create_image_from_b64(contact, data, contact.user)

    create_or_update_organisation(contact, data, user, history)

    _format_data(contact, data)

    write_simple_history(history, data)

    contact.__dict__.update(data) #TODO: setattr better ?
    contact.save()

    history.save()

    return contact

def write_simple_history(history, data):
    changes = []
    for ns, fields in CREME_CONTACT_MAPPING.iteritems():
        for creme_field in fields.iterkeys():
            updated = data.get(creme_field)
            if updated is not None:
                changes.append((creme_field, updated.encode('utf-8')))#Adding changes to the history
            #else tell the attr was emptied?

    history.changes = changes

def serialize_contact(contact, namespaces):
    """Serialize a contact in xml respecting namespaces prefixes
       TODO/NB: Need to send an empty value when the contact hasn't a value ?
       TODO: Add the possibility to subset contact fields ?
    """
    xml = []
    xml_append = xml.append

    for ns, values in CREME_CONTACT_MAPPING.iteritems():
        prefix = namespaces.get(ns)

        for c_field, xml_field in values.iteritems():
            value = None

            if callable(c_field):
                value = c_field(contact)
            else:
                f_class, value = get_instance_field_info(contact, c_field)

            if value:
                xml_append("<%(prefix)s%(tag)s>%(value)s</%(prefix)s%(tag)s>" % {
                                'prefix': '%s:' % prefix if prefix else '',
                                'tag':    xml_field,
                                'value':  value, #Problems with unicode
                            }
                           )

    return "".join(xml)

def pre_serialize_contact(value, c_field, xml_field, f_class, entity):
    return value
