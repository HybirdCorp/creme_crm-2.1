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

from collections import defaultdict

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db.models import Count
from django.utils.translation import ugettext_lazy as _, ugettext

from creme.creme_core.core.setting_key import setting_key_registry
from creme.creme_core.gui.block import Block, PaginatedBlock, QuerysetBlock, block_registry
from creme.creme_core.models import (CremeModel, CremeEntity, UserRole, SettingValue,
        CremePropertyType, RelationType, SemiFixedRelationType, FieldsConfig,
        CustomField, CustomFieldEnumValue,
        BlockDetailviewLocation, BlockPortalLocation, BlockMypageLocation,
        RelationBlockItem, InstanceBlockConfigItem, CustomBlockConfigItem,
        ButtonMenuItem, SearchConfigItem, HistoryConfigItem, PreferedMenuItem)
from creme.creme_core.registry import creme_registry
from creme.creme_core.utils import creme_entity_content_types
from creme.creme_core.utils.unicode_collation import collator

#from .models import SettingValue


_PAGE_SIZE = 20
User = get_user_model()


class GenericModelsBlock(QuerysetBlock):
    id_           = QuerysetBlock.generate_id('creme_config', 'model_config')
    dependencies  = (CremeModel,)
    #order_by      = 'id'
    page_size     = _PAGE_SIZE
    verbose_name  = u'Model configuration'
    template_name = 'creme_config/templatetags/block_models.html'
    configurable  = False

    def detailview_display(self, context):
        # NB: credentials are OK : we are sure to use the custom reloading view
        #     if 'model', 'model_name' etc... are in the context
        model = context['model']

        try:
            #self.order_by = model._meta.ordering[0] #TODO: uncomment when the block is not a singleton any more.... (beware if a 'order' field exists - see template)
            order_by = model._meta.ordering[0]
        except IndexError:
            order_by = 'id'

        meta = model._meta
        fields = meta.fields
        many_to_many = meta.many_to_many

        colspan = len(fields) + len(many_to_many) + 2 # "2" is for 'edit' & 'delete' actions
        if any(field.name == 'is_custom' for field in fields):
            colspan -= 1

        return self._render(self.get_block_template_context(
                                context, model.objects.order_by(order_by),
                                update_url='/creme_config/models/%s/reload/' % ContentType.objects.get_for_model(model).id,
                                model=model,
                                model_name=context['model_name'],
                                app_name=context['app_name'],
                                fields=meta.fields,
                                many_to_many=many_to_many,
                                colspan=colspan,
                           ))


class SettingsBlock(QuerysetBlock):
    id_           = QuerysetBlock.generate_id('creme_config', 'settings')
    dependencies  = (SettingValue,)
    page_size     = _PAGE_SIZE
    verbose_name  = u'App settings'
    template_name = 'creme_config/templatetags/block_settings.html'
    configurable  = False

    def detailview_display(self, context):
        app_name = context['app_name']

        skeys_ids = [skey.id
                        for skey in setting_key_registry
                            if skey.app_label == app_name and not skey.hidden
                    ]

        return self._render(self.get_block_template_context(
                                context,
                                SettingValue.objects.filter(key_id__in=skeys_ids, user=None),
                                update_url='/creme_config/settings/%s/reload/' % app_name,
                                app_name=app_name,
                           ))


class _ConfigAdminBlock(QuerysetBlock):
    page_size    = _PAGE_SIZE
#    permission   = 'creme_config.can_admin' #NB: used by the view creme_core.views.blocks.reload_basic
    permission   = None # The portals can be viewed by all users => reloading can be done by all uers too.
    configurable = False


class PropertyTypesBlock(_ConfigAdminBlock):
    id_           = _ConfigAdminBlock.generate_id('creme_config', 'property_types')
    dependencies  = (CremePropertyType,)
    order_by      = 'text'
    verbose_name  = _(u'Property types configuration')
    template_name = 'creme_config/templatetags/block_property_types.html'

    def detailview_display(self, context):
        return self._render(self.get_block_template_context(
                                context,
                                CremePropertyType.objects.annotate(stats=Count('cremeproperty')),
                                update_url='/creme_core/blocks/reload/basic/%s/' % self.id_,
                           ))


class RelationTypesBlock(_ConfigAdminBlock):
    id_           = _ConfigAdminBlock.generate_id('creme_config', 'relation_types')
    dependencies  = (RelationType,)
    verbose_name  = _(u'List of standard relation types')
    template_name = 'creme_config/templatetags/block_relation_types.html'

    def detailview_display(self, context):
        return self._render(self.get_block_template_context(
                                context,
                                RelationType.objects.filter(is_custom=False,
                                                            pk__contains='-subject_',
                                                           ),
                                update_url='/creme_core/blocks/reload/basic/%s/' % self.id_,
                                custom=False,
                           ))


class CustomRelationTypesBlock(_ConfigAdminBlock):
    id_           = _ConfigAdminBlock.generate_id('creme_config', 'custom_relation_types')
    dependencies  = (RelationType,)
    verbose_name  = _(u'Custom relation types configuration')
    template_name = 'creme_config/templatetags/block_relation_types.html'

    def detailview_display(self, context):
        return self._render(self.get_block_template_context(
                                context,
                                RelationType.objects.filter(is_custom=True,
                                                            pk__contains='-subject_',
                                                           ),
                                update_url='/creme_core/blocks/reload/basic/%s/' % self.id_,
                                custom=True,
                            ))


class SemiFixedRelationTypesBlock(_ConfigAdminBlock):
    id_           = _ConfigAdminBlock.generate_id('creme_config', 'semifixed_relation_types')
    dependencies  = (RelationType, SemiFixedRelationType,)
    verbose_name  = _(u'List of semi-fixed relation types')
    template_name = 'creme_config/templatetags/block_semifixed_relation_types.html'

    def detailview_display(self, context):
        btc = self.get_block_template_context(context, SemiFixedRelationType.objects.all(),
                                              update_url='/creme_core/blocks/reload/basic/%s/' % self.id_,
                                             )

        CremeEntity.populate_real_entities([sfrt.object_entity for sfrt in btc['page'].object_list])

        return self._render(btc)


class FieldsConfigsBlock(PaginatedBlock):
    id_           = PaginatedBlock.generate_id('creme_config', 'fields_configs')
    dependencies  = (FieldsConfig,)
    page_size     = _PAGE_SIZE
    verbose_name  = u'Fields configuration'
    template_name = 'creme_config/templatetags/block_fields_configs.html'
#    permission    = 'creme_config.can_admin' # NB: used by the view creme_core.views.blocks.reload_basic
    permission    = None # NB: used by the view creme_core.views.blocks.reload_basic()
    configurable  = False

    def detailview_display(self, context):
        # TODO: exclude CTs that user cannot see ? (should probably done everywhere in creme_config...)
        fconfigs = list(FieldsConfig.objects.all())
        sort_key = collator.sort_key
        fconfigs.sort(key=lambda fconf: sort_key(unicode(fconf.content_type)))

        btc = self.get_block_template_context(
                    context, fconfigs,
                    update_url='/creme_core/blocks/reload/basic/%s/' % self.id_,
                )

        for fconf in btc['page'].object_list:
            vnames = [unicode(f.verbose_name) for f in fconf.hidden_fields]
            vnames.sort(key=sort_key)

            fconf.fields_vnames = vnames

        return self._render(btc)


class CustomFieldsPortalBlock(_ConfigAdminBlock):
    id_           = _ConfigAdminBlock.generate_id('creme_config', 'custom_fields_portal')
    dependencies  = (CustomField,)
    verbose_name  = _(u'General configuration of custom fields')
    template_name = 'creme_config/templatetags/block_custom_fields_portal.html'

    def detailview_display(self, context):
        ct_ids = CustomField.objects.distinct().values_list('content_type_id', flat=True)

        return self._render(self.get_block_template_context(
                                context, ContentType.objects.filter(pk__in=ct_ids),
                                update_url='/creme_core/blocks/reload/basic/%s/' % self.id_,
                           ))


class CustomFieldsBlock(QuerysetBlock):
    id_           = QuerysetBlock.generate_id('creme_config', 'custom_fields')
    dependencies  = (CustomField,)
    page_size     = _PAGE_SIZE
    verbose_name  = _(u'Custom fields configuration')
    template_name = 'creme_config/templatetags/block_custom_fields.html'
    configurable  = False

    def detailview_display(self, context):
        # NB: credentials are OK : we are sure to use the custom reloading view if 'content_type' is in the context
        ct = context['content_type'] #ct_id instead ??

        btc = self.get_block_template_context(
                    context, CustomField.objects.filter(content_type=ct),
                    update_url='/creme_config/custom_fields/%s/reload/' % ct.id,
                    ct=ct
                )

        # Retrieve & cache Enum values (in order to display them of course)
        enums_types = {CustomField.ENUM, CustomField.MULTI_ENUM}
        enums_cfields = [cfield
                            for cfield in btc['page'].object_list
                                if cfield.field_type in enums_types
                        ]
        evalues_map = defaultdict(list)

        for enum_value in CustomFieldEnumValue.objects.filter(custom_field__in=enums_cfields):
            evalues_map[enum_value.custom_field_id].append(enum_value.value)

        for enums_cfield in enums_cfields:
            enums_cfield.enum_values = evalues_map[enums_cfield.id]

        return self._render(btc)


class UsersBlock(_ConfigAdminBlock):
    id_           = _ConfigAdminBlock.generate_id('creme_config', 'users')
    dependencies  = (User,)
    order_by      = 'username'
    verbose_name  = _(u'Users configuration')
    template_name = 'creme_config/templatetags/block_users.html'

    def detailview_display(self, context):
        users = User.objects.filter(is_team=False)
        if not context['user'].is_staff:
            users = users.exclude(is_staff=True)
        return self._render(self.get_block_template_context(
                                context, users,
                                update_url='/creme_core/blocks/reload/basic/%s/' % self.id_,
                           ))


class TeamsBlock(_ConfigAdminBlock):
    id_           = _ConfigAdminBlock.generate_id('creme_config', 'teams')
    dependencies  = (User,)
    order_by      = 'username'
    verbose_name  = u'Teams configuration'
    template_name = 'creme_config/templatetags/block_teams.html'

    def detailview_display(self, context):
        return self._render(self.get_block_template_context(
                                context, User.objects.filter(is_team=True),
                                update_url='/creme_core/blocks/reload/basic/%s/' % self.id_,
                           ))


#class BlockDetailviewLocationsBlock(_ConfigAdminBlock):
class BlockDetailviewLocationsBlock(PaginatedBlock):
#    id_           = _ConfigAdminBlock.generate_id('creme_config', 'blocks_dv_locations')
    id_           = PaginatedBlock.generate_id('creme_config', 'blocks_dv_locations')
    dependencies  = (BlockDetailviewLocation,)
    page_size     = _PAGE_SIZE - 1 #'-1' because there is always the line for default config on each page
    verbose_name  = u'Blocks locations on detailviews'
    template_name = 'creme_config/templatetags/block_blocklocations.html'
#    permission    = 'creme_config.can_admin' #NB: used by the view creme_core.views.blocks.reload_basic
    permission    = None #NB: used by the view creme_core.views.blocks.reload_basic
    configurable  = False

    def detailview_display(self, context):
#        ct_ids = BlockDetailviewLocation.objects.exclude(content_type=None)\
#                                                .distinct()\
#                                                .values_list('content_type_id', flat=True)
#
#        return self._render(self.get_block_template_context(
#                                context, ContentType.objects.filter(pk__in=ct_ids), #todo: use get_for_id instead (avoid query) ??
#                                update_url='/creme_core/blocks/reload/basic/%s/' % self.id_,
#                           ))
        # NB: we wrap the ContentType instances instead of store extra data in
        #     them because teh instances are stored in a global cache, so we do
        #     not want to mutate them.
        class _ContentTypeWrapper(object): # TODO: move from here ?
            __slots__ = ('ctype', 'locations_info', 'default_count')

            def __init__(self, ctype):
                self.ctype = ctype
                self.default_count = 0
                self.locations_info = () # List of tuples (role_arg, role_label, block_count)
                                         # with role_arg == role.id or 'superuser'

        # TODO: factorise with SearchConfigBlock ?
        # TODO: factorise with CustomBlockConfigItemCreateForm , add a method in block_registry ?
#        ctypes = [_ContentTypeWrapper(ctype) for ctype in creme_entity_content_types()]
        get_ct = ContentType.objects.get_for_model
        is_invalid = block_registry.is_model_invalid
        ctypes = [_ContentTypeWrapper(get_ct(model))
                      for model in creme_registry.iter_entity_models()
                          if not is_invalid(model)
                 ]

        sort_key = collator.sort_key
        ctypes.sort(key=lambda ctw: sort_key(unicode(ctw.ctype)))

        btc = self.get_block_template_context(
                        context, ctypes,
                        update_url='/creme_core/blocks/reload/basic/%s/' % self.id_,
                        max_conf_count=UserRole.objects.count() + 1, # NB: '+ 1' is for super-users config.
                    )

        ctypes_wrappers = btc['page'].object_list

        block_counts = defaultdict(lambda: defaultdict(int)) # block_counts[content_type.id][(role_id, superuser)] -> count
        role_ids = set()

        for bdl in BlockDetailviewLocation.objects \
                                          .filter(content_type__in=[ctw.ctype for ctw in ctypes_wrappers]):
            if bdl.block_id: # do not count the 'place-holder' (empty block IDs which mean "no-block for this zone")
                role_id = bdl.role_id
                block_counts[bdl.content_type_id][(role_id, bdl.superuser)] += 1
                role_ids.add(role_id)

        role_names = dict(UserRole.objects.filter(id__in=role_ids).values_list('id', 'name'))
        superusers_label = ugettext('Superuser') # TODO: cached_lazy_ugettext

        for ctw in ctypes_wrappers:
            count_per_role = block_counts[ctw.ctype.id]
            ctw.default_count = count_per_role.pop((None, False), 0)

            ctw.locations_info = locations_info = []
            for (role_id, superuser), block_count in count_per_role.iteritems():
                if superuser:
                    role_arg = 'superuser'
                    role_label = superusers_label
                else:
                    role_arg = role_id
                    role_label = role_names[role_id]

                locations_info.append((role_arg, role_label, block_count))

            locations_info.sort(key=lambda t: sort_key(t[1])) # sort by role label

        btc['default_count'] = BlockDetailviewLocation.objects.filter(content_type=None,
                                                                      role=None, superuser=False,
                                                                     ).count()

        return self._render(btc)


class BlockPortalLocationsBlock(PaginatedBlock):
    id_           = PaginatedBlock.generate_id('creme_config', 'blocks_portal_locations')
    dependencies  = (BlockPortalLocation,)
    page_size     = _PAGE_SIZE - 2 #'-1' because there is always the line for default config & home config on each page
    verbose_name  = u'Blocks locations on portals'
    template_name = 'creme_config/templatetags/block_blockportallocations.html'
#    permission    = 'creme_config.can_admin' #NB: used by the view creme_core.views.blocks.reload_basic
    permission    = None #NB: used by the view creme_core.views.blocks.reload_basic()
    configurable  = False

    def detailview_display(self, context):
        get_app = creme_registry.get_app
        apps = [get_app(name) for name in BlockPortalLocation.objects.exclude(app_name='creme_core')
                                                             .order_by('app_name') #in order that distinct() works correctly
                                                             .distinct()
                                                             .values_list('app_name', flat=True)
                                  if name
               ]

        sort_key = collator.sort_key
        apps.sort(key=lambda app: sort_key(app.verbose_name))

        return self._render(self.get_block_template_context(
                                context, apps,
                                update_url='/creme_core/blocks/reload/basic/%s/' % self.id_,
                           ))


#class BlockDefaultMypageLocationsBlock(PaginatedBlock):
class BlockDefaultMypageLocationsBlock(_ConfigAdminBlock):
#    id_           = QuerysetBlock.generate_id('creme_config', 'blocks_default_mypage_locations')
    id_           = _ConfigAdminBlock.generate_id('creme_config', 'blocks_default_mypage_locations')
    dependencies  = (BlockMypageLocation,)
#    page_size     = _PAGE_SIZE
    verbose_name  = u'Default blocks locations on "My page"'
    template_name = 'creme_config/templatetags/block_blockdefmypagelocations.html'
#    permission    = 'creme_config.can_admin' #NB: used by the view creme_core.views.blocks.reload_basic
#    configurable  = False

    def detailview_display(self, context):
        return self._render(self.get_block_template_context(
                                context,
                                BlockMypageLocation.objects.filter(user=None),
                                update_url='/creme_core/blocks/reload/basic/%s/' % self.id_,
                           ))


#class BlockMypageLocationsBlock(PaginatedBlock):
class BlockMypageLocationsBlock(_ConfigAdminBlock):
#    id_           = QuerysetBlock.generate_id('creme_config', 'blocks_mypage_locations')
    id_           = _ConfigAdminBlock.generate_id('creme_config', 'blocks_mypage_locations')
    dependencies  = (BlockMypageLocation,)
#    page_size     = _PAGE_SIZE
    verbose_name  = u'Blocks locations on "My page"'
    template_name = 'creme_config/templatetags/block_blockmypagelocations.html'
#    permission    = 'creme_config.can_admin' #NB: used by the view creme_core.views.blocks.reload_basic
#    configurable  = False

    def detailview_display(self, context):
        return self._render(self.get_block_template_context(
                                context,
                                BlockMypageLocation.objects.filter(user=context['user']),
                                update_url='/creme_core/blocks/reload/basic/%s/' % self.id_,
                           ))


class RelationBlocksConfigBlock(_ConfigAdminBlock):
    id_           = _ConfigAdminBlock.generate_id('creme_config', 'relation_blocks_config')
    dependencies  = (RelationBlockItem, BlockDetailviewLocation) #BlockDetailviewLocation because they can be deleted if we delete a RelationBlockItem
    verbose_name  = u'Relation blocks configuration'
    template_name = 'creme_config/templatetags/block_relationblocksconfig.html'

    def detailview_display(self, context):
        return self._render(self.get_block_template_context(
                                context, RelationBlockItem.objects.all(),
                                update_url='/creme_core/blocks/reload/basic/%s/' % self.id_,
                           ))


class InstanceBlocksConfigBlock(_ConfigAdminBlock):
    id_           = _ConfigAdminBlock.generate_id('creme_config', 'instance_blocks_config')
    dependencies  = (InstanceBlockConfigItem, BlockDetailviewLocation) #BlockDetailviewLocation because they can be deleted if we delete a InstanceBlockConfigItem
    verbose_name  = u'Instance blocks configuration'
    template_name = 'creme_config/templatetags/block_instanceblocksconfig.html'

    def detailview_display(self, context):
        return self._render(self.get_block_template_context(
                                context, InstanceBlockConfigItem.objects.all(),
                                update_url='/creme_core/blocks/reload/basic/%s/' % self.id_,
                           ))


class CustomBlocksConfigBlock(_ConfigAdminBlock):
    id_           = _ConfigAdminBlock.generate_id('creme_config', 'custom_blocks_config')
    dependencies  = (CustomBlockConfigItem,)
    verbose_name  = u'Custom blocks configuration'
    template_name = 'creme_config/templatetags/block_customblocksconfig.html'

    def detailview_display(self, context):
        return self._render(self.get_block_template_context(
                                context, CustomBlockConfigItem.objects.all(),
                                update_url='/creme_core/blocks/reload/basic/%s/' % self.id_,
                           ))


#class ButtonMenuBlock(_ConfigAdminBlock):
class ButtonMenuBlock(Block):
    #id_           = QuerysetBlock.generate_id('creme_config', 'button_menu')
    id_           = Block.generate_id('creme_config', 'button_menu')
    dependencies  = (ButtonMenuItem,)
    verbose_name  = u'Button menu configuration'
    template_name = 'creme_config/templatetags/block_button_menu.html'
#    permission    = 'creme_config.can_admin' #NB: used by the view creme_core.views.blocks.reload_basic
    permission    = None #NB: used by the view creme_core.views.blocks.reload_basic()
    configurable  = False

    def detailview_display(self, context):
        buttons_map = defaultdict(list)

        for bmi in ButtonMenuItem.objects.order_by('order'): #TODO: meta.ordering...
            buttons_map[bmi.content_type_id].append(bmi)

        build_verbose_names = lambda bm_items: [unicode(bmi) for bmi in bm_items if bmi.button_id]
        default_buttons = build_verbose_names(buttons_map.pop(None, ()))

        get_ct = ContentType.objects.get_for_id
        buttons = [(get_ct(ct_id), build_verbose_names(bm_items))
                        for ct_id, bm_items in buttons_map.iteritems()
                  ]
        sort_key = collator.sort_key
        buttons.sort(key=lambda t: sort_key(unicode(t[0])))

        return self._render(self.get_block_template_context(
                                context,
                                default_buttons=default_buttons,
                                buttons=buttons,
                                update_url='/creme_core/blocks/reload/basic/%s/' % self.id_,
                           ))


#class SearchConfigBlock(_ConfigAdminBlock):
class SearchConfigBlock(PaginatedBlock):
#    id_           = _ConfigAdminBlock.generate_id('creme_config', 'searchconfig')
    id_           = PaginatedBlock.generate_id('creme_config', 'searchconfig')
    dependencies  = (SearchConfigItem,)
    verbose_name  = u'Search configuration'
    template_name = 'creme_config/templatetags/block_searchconfig.html'
    order_by      = 'content_type'
    # TODO _ConfigAdminBlock => Mixin
    page_size    = _PAGE_SIZE * 2 # only one block
#    permission   = 'creme_config.can_admin' #NB: used by the view creme_core.views.blocks.reload_basic
    permission   = None # NB: used by the view creme_core.views.blocks.reload_basic()
    configurable = False

    def detailview_display(self, context):
#        return self._render(self.get_block_template_context(
#                                context, SearchConfigItem.objects.all(),
#                                update_url='/creme_core/blocks/reload/basic/%s/' % self.id_,
#                           ))
        # NB: we wrap the ContentType instances instead of store extra data in
        #     them because teh instances are stored in a global cache, so we do
        #     not want to mutate them.
        class _ContentTypeWrapper(object): # TODO: move from here ?
            __slots__ = ('ctype', 'sc_items')

            def __init__(self, ctype):
                self.ctype = ctype
                self.sc_items = ()

        ctypes = [_ContentTypeWrapper(ctype) for ctype in creme_entity_content_types()]
        sort_key = collator.sort_key
        ctypes.sort(key=lambda ctw: sort_key(unicode(ctw.ctype)))

        btc = self.get_block_template_context(
                        context, ctypes,
                        update_url='/creme_core/blocks/reload/basic/%s/' % self.id_,
#                        max_conf_count=User.objects.exclude(is_team=True).count() + 1, # NB: '+ 1' is for default config
                        max_conf_count=UserRole.objects.count() + 2, # NB: '+ 2' is for default config + super-users config.
                    )

        ctypes_wrappers = btc['page'].object_list

        sci_map = defaultdict(list)
        for sci in SearchConfigItem.objects \
                                   .filter(content_type__in=[ctw.ctype for ctw in ctypes_wrappers])\
                                   .select_related('role'):
#                                   .select_related('user'):
            sci_map[sci.content_type_id].append(sci)

        superusers_label = ugettext('Superuser')

        for ctw in ctypes_wrappers:
            ctype = ctw.ctype
            ctw.sc_items = sc_items = sci_map.get(ctype.id) or []
#            sc_items.sort(key=lambda sci: sort_key(unicode(sci.user) if sci.user else ''))
            sc_items.sort(key=lambda sci: sort_key(unicode(sci.role) if sci.role
                                                   else superusers_label if sci.superuser
                                                   else ''
                                                  )
                         )

#            if not sc_items or sc_items[0].user: # No default config -> we build it
            if not sc_items or not sc_items[0].is_default:  # No default config -> we build it
                SearchConfigItem.objects.create(content_type=ctype)

        return self._render(btc)


class HistoryConfigBlock(_ConfigAdminBlock):
    id_           = _ConfigAdminBlock.generate_id('creme_config', 'historyconfig')
    dependencies  = (HistoryConfigItem,)
    verbose_name  = u'History configuration'
    template_name = 'creme_config/templatetags/block_historyconfig.html'

    def detailview_display(self, context):
        return self._render(self.get_block_template_context(
                                context, HistoryConfigItem.objects.all(),
                                update_url='/creme_core/blocks/reload/basic/%s/' % self.id_,
                           ))


class UserRolesBlock(_ConfigAdminBlock):
    id_           = _ConfigAdminBlock.generate_id('creme_config', 'user_roles')
    dependencies  = (UserRole,)
    order_by      = 'name'
    verbose_name  = u'User roles configuration'
    template_name = 'creme_config/templatetags/block_user_roles.html'

    def detailview_display(self, context):
        return self._render(self.get_block_template_context(
                                context, UserRole.objects.all(),
                                update_url='/creme_core/blocks/reload/basic/%s/' % self.id_,
                           ))


class UserPreferedMenusBlock(QuerysetBlock):
    id_           = QuerysetBlock.generate_id('creme_config', 'user_prefered_menus')
    dependencies  = (PreferedMenuItem,)
    verbose_name  = u'My prefered menus'
    template_name = 'creme_config/templatetags/block_user_prefered_menus.html'
    configurable  = False
    order_by      = 'order'
    permission    = None #NB: used by the view creme_core.views.blocks.reload_basic ; None means 'No special permission required'

    def detailview_display(self, context):
        #NB: credentials OK: user can only view his own settings
        return self._render(self.get_block_template_context(
                                context,
                                PreferedMenuItem.objects.filter(user=context['user']),
                                page_size=self.page_size,
                                update_url='/creme_core/blocks/reload/basic/%s/' % self.id_,
                           ))


generic_models_block = GenericModelsBlock()
settings_block       = SettingsBlock()
custom_fields_block  = CustomFieldsBlock()

blocks_list = (
        generic_models_block,
        settings_block,
        PropertyTypesBlock(),
        RelationTypesBlock(),
        CustomRelationTypesBlock(),
        SemiFixedRelationTypesBlock(),
        CustomFieldsPortalBlock(),
        custom_fields_block,
        BlockDetailviewLocationsBlock(),
        BlockPortalLocationsBlock(),
        BlockDefaultMypageLocationsBlock(),
        BlockMypageLocationsBlock(),
        RelationBlocksConfigBlock(),
        InstanceBlocksConfigBlock(),
        FieldsConfigsBlock(),
        CustomBlocksConfigBlock(),
        ButtonMenuBlock(),
        UsersBlock(),
        TeamsBlock(),
        SearchConfigBlock(),
        HistoryConfigBlock(),
        UserRolesBlock(),
        UserPreferedMenusBlock(),
    )
