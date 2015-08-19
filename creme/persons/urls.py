# -*- coding: utf-8 -*-

from django.conf.urls import url

from . import address_model_is_custom, contact_model_is_custom, organisation_model_is_custom
from .views import portal, crud_relations


urlpatterns = [
    url(r'^$', portal.portal),

    url(r'^(?P<entity_id>\d+)/become_customer$',          crud_relations.become_customer),
    url(r'^(?P<entity_id>\d+)/become_prospect$',          crud_relations.become_prospect),
    url(r'^(?P<entity_id>\d+)/become_suspect$',           crud_relations.become_suspect),
    url(r'^(?P<entity_id>\d+)/become_inactive_customer$', crud_relations.become_inactive),
    url(r'^(?P<entity_id>\d+)/become_supplier$',          crud_relations.become_supplier),
]

if not contact_model_is_custom():
    from .views import contact

    urlpatterns += [
        url(r'^contacts$',                                                        contact.listview,          name='persons__list_contacts'),
        url(r'^contact/add$',                                                     contact.add,               name='persons__create_contact'),
        url(r'^contact/add_with_relation/(?P<orga_id>\d+)$',                      contact.add_with_relation, name='persons__create_related_contact'),
        #url(r'^contact/add_with_relation/(?P<orga_id>\d+)/(?P<predicate_id>[\w-]+)$', 'add_with_relation', name='persons__create_related_contact'),
        url(r'^contact/add_with_relation/(?P<orga_id>\d+)/(?P<rtype_id>[\w-]+)$', contact.add_with_relation, name='persons__create_related_contact'),
        url(r'^contact/edit/(?P<contact_id>\d+)$',                                contact.edit,              name='persons__edit_contact'),
        url(r'^contact/(?P<contact_id>\d+)$',                                     contact.detailview,        name='persons__view_contact'),
    ]

if not organisation_model_is_custom():
    from .views import organisation

    urlpatterns += [
        url(r'^organisations$',                              organisation.listview,                   name='persons__list_organisations'),
        url(r'^organisation/add$',                           organisation.add,                        name='persons__create_organisation'),
        url(r'^organisation/edit/(?P<organisation_id>\d+)$', organisation.edit,                       name='persons__edit_organisation'),
        url(r'^organisation/(?P<organisation_id>\d+)$',      organisation.detailview,                 name='persons__view_organisation'),
        url(r'^leads_customers$',                            organisation.list_my_leads_my_customers, name='persons__leads_customers'),
    ]

if not address_model_is_custom():
    from .views import address

    urlpatterns += [
        url(r'^address/add/(?P<entity_id>\d+)$',          address.add,          name='persons__create_address'),
        url(r'^address/add/billing/(?P<entity_id>\d+)$',  address.add_billing,  name='persons__create_billing_address'),
        url(r'^address/add/shipping/(?P<entity_id>\d+)$', address.add_shipping, name='persons__create_shipping_address'),
        url(r'^address/edit/(?P<address_id>\d+)',         address.edit,         name='persons__edit_address'),
    ]
