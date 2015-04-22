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

from django.core.urlresolvers import reverse_lazy as reverse
from django.utils.translation import ugettext_lazy as _

from creme.creme_core.auth import build_creation_perm
from creme.creme_core.registry import creme_registry
from creme.creme_core.gui import creme_menu, block_registry, icon_registry, bulk_update_registry

from . import get_product_model, get_service_model
from .blocks import images_block
#from .models import Product, Service
from .forms.product import ProductInnerEditCategory


Product = get_product_model()
Service = get_service_model()

creme_registry.register_app('products', _(u'Products and services'), '/products')
creme_registry.register_entity_models(Product, Service)

reg_item = creme_menu.register_app('products', '/products/').register_item
reg_item('/products/',            _(u'Portal of products and services'), 'products')
#reg_item('/products/products',    _(u'All products'),                    'products')
#reg_item('/products/product/add', Product.creation_label,                'products.add_product')
#reg_item('/products/services',    _(u'All services'),                    'products')
#reg_item('/products/service/add', Service.creation_label,                'products.add_service')
reg_item(reverse('products__list_products'),  _(u'All products'),     'products')
reg_item(reverse('products__create_product'), Product.creation_label, build_creation_perm(Product))
reg_item(reverse('products__list_services'),  _(u'All services'),     'products')
reg_item(reverse('products__create_service'), Service.creation_label, build_creation_perm(Service))

block_registry.register(images_block)

reg_icon = icon_registry.register
reg_icon(Product, 'images/product_%(size)s.png')
reg_icon(Service, 'images/service_%(size)s.png')

bulk_update_registry.register(Product, innerforms={'category':     ProductInnerEditCategory,
                                                   'sub_category': ProductInnerEditCategory})

bulk_update_registry.register(Service, innerforms={'category':     ProductInnerEditCategory,
                                                   'sub_category': ProductInnerEditCategory})
