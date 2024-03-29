# -*- coding: utf-8 -*-

################################################################################
#    Creme is a free/open-source Customer Relationship Management software
#    Copyright (C) 2009-2021  Hybird
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
import logging

from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db.models import Count
from django.utils.translation import gettext_lazy as _, gettext

from creme.creme_core.core import setting_key
from creme.creme_core.gui.bricks import (Brick, PaginatedBrick, QuerysetBrick,
        brick_registry, BricksManager)
from creme.creme_core.models import (CremeModel, CremeEntity, UserRole, SettingValue,
        CremePropertyType, RelationType, SemiFixedRelationType, FieldsConfig,
        CustomField, CustomFieldEnumValue,
        BrickDetailviewLocation, BrickHomeLocation, BrickMypageLocation,
        RelationBrickItem, InstanceBrickConfigItem, CustomBrickConfigItem,
        ButtonMenuItem, SearchConfigItem, HistoryConfigItem)
from creme.creme_core.registry import creme_registry
from creme.creme_core.utils import creme_entity_content_types
from creme.creme_core.utils.unicode_collation import collator

from .constants import BRICK_STATE_HIDE_INACTIVE_USERS

_PAGE_SIZE = 20
User = get_user_model()
logger = logging.getLogger(__name__)


class GenericModelBrick(QuerysetBrick):
    id_           = QuerysetBrick.generate_id('creme_config', 'model_config')
    dependencies  = (CremeModel,)
    page_size     = _PAGE_SIZE
    verbose_name  = 'Model configuration'
    template_name = 'creme_config/bricks/configurable-model.html'
    configurable  = False

    # NB: credentials are OK : we are sure to use the custom reloading view because of the specific constructor.
    # def __init__(self, app_name, model_name, model):
    def __init__(self, app_name, model_config):
        super().__init__()
        self.app_name = app_name
        # self.model_name = model_name
        # self.model = model
        self.model_config = model_config

    def detailview_display(self, context):
        # model = self.model
        model_config = self.model_config
        model = model_config.model
        meta = model._meta

        # TODO: (must declare in the template what fields can be used to sort)
        # ordering = meta.ordering
        # if ordering:
        #     self.order_by = ordering[0]

        displayable_fields = []
        is_reorderable = False

        for field in meta.fields:
            fieldname = field.name.lower()

            if fieldname == 'is_custom':
                continue
            elif fieldname == 'order':
                is_reorderable = True
            else:
                displayable_fields.append(field)

        displayable_fields.extend(meta.many_to_many)

        return self._render(self.get_template_context(
                    context,
                    model.objects.all(),

                    model=model,
                    meta=meta,

                    app_name=self.app_name,
                    model_config=model_config,
                    # model_name=self.model_name,

                    model_is_reorderable=is_reorderable,
                    displayable_fields=displayable_fields,
        ))


class SettingsBrick(QuerysetBrick):
    id_           = QuerysetBrick.generate_id('creme_config', 'settings')
    dependencies  = (SettingValue,)
    page_size     = _PAGE_SIZE
    verbose_name  = 'App settings'
    template_name = 'creme_config/bricks/setting-values.html'
    configurable  = False
    order_by      = 'id'

    setting_key_registry = setting_key.setting_key_registry

    def detailview_display(self, context):
        app_name = context['app_name']
        skeys_ids = [skey.id
                        for skey in self.setting_key_registry
                            if skey.app_label == app_name and not skey.hidden
                    ]

        return self._render(self.get_template_context(
                                context,
                                SettingValue.objects.filter(key_id__in=skeys_ids),
                                app_name=app_name,
                           ))


class _ConfigAdminBrick(QuerysetBrick):
    page_size    = _PAGE_SIZE
    permission   = None  # The portals can be viewed by all users => reloading can be done by all users too.
    configurable = False


class PropertyTypesBrick(_ConfigAdminBrick):
    id_           = _ConfigAdminBrick.generate_id('creme_config', 'property_types')
    dependencies  = (CremePropertyType,)
    order_by      = 'text'
    verbose_name  = _('Property types configuration')
    template_name = 'creme_config/bricks/property-types.html'

    def detailview_display(self, context):
        return self._render(self.get_template_context(
                    context,
                    CremePropertyType.objects.annotate(stats=Count('cremeproperty')),
        ))


class RelationTypesBrick(_ConfigAdminBrick):
    id_           = _ConfigAdminBrick.generate_id('creme_config', 'relation_types')
    dependencies  = (RelationType,)
    verbose_name  = _('List of standard relation types')
    template_name = 'creme_config/bricks/relation-types.html'

    def detailview_display(self, context):
        return self._render(self.get_template_context(
                    context,
                    RelationType.objects.filter(is_custom=False,
                                                pk__contains='-subject_',
                                               ),
                    custom=False,
        ))


class CustomRelationTypesBrick(_ConfigAdminBrick):
    id_           = _ConfigAdminBrick.generate_id('creme_config', 'custom_relation_types')
    dependencies  = (RelationType,)
    verbose_name  = _('Custom relation types configuration')
    template_name = 'creme_config/bricks/relation-types.html'

    def detailview_display(self, context):
        return self._render(self.get_template_context(
                    context,
                    RelationType.objects.filter(is_custom=True,
                                                pk__contains='-subject_',
                                               ),
                    custom=True,
        ))


class SemiFixedRelationTypesBrick(_ConfigAdminBrick):
    id_           = _ConfigAdminBrick.generate_id('creme_config', 'semifixed_relation_types')
    dependencies  = (RelationType, SemiFixedRelationType,)
    verbose_name  = _('List of semi-fixed relation types')
    template_name = 'creme_config/bricks/semi-fixed-relation-types.html'

    def detailview_display(self, context):
        btc = self.get_template_context(
                    context, SemiFixedRelationType.objects.all(),
        )

        CremeEntity.populate_real_entities([sfrt.object_entity for sfrt in btc['page'].object_list])

        return self._render(btc)


class FieldsConfigsBrick(PaginatedBrick):
    id_           = PaginatedBrick.generate_id('creme_config', 'fields_configs')
    dependencies  = (FieldsConfig,)
    page_size     = _PAGE_SIZE
    verbose_name  = 'Fields configuration'
    template_name = 'creme_config/bricks/fields-configs.html'
    permission    = None  # NB: used by the view creme_core.views.bricks.reload_basic()
    configurable  = False

    def detailview_display(self, context):
        # TODO: exclude CTs that user cannot see ? (should probably done everywhere in creme_config...)
        fconfigs = [*FieldsConfig.objects.all()]
        sort_key = collator.sort_key
        fconfigs.sort(key=lambda fconf: sort_key(str(fconf.content_type)))

        used_models = {fconf.content_type.model_class() for fconf in fconfigs}
        btc = self.get_template_context(
            context, fconfigs,
            display_add_button=any(model not in used_models
                                       for model in filter(FieldsConfig.is_model_valid, apps.get_models())
                                  ),
        )

        for fconf in btc['page'].object_list:
            vnames = [str(f.verbose_name) for f in fconf.hidden_fields]
            vnames.sort(key=sort_key)

            fconf.fields_vnames = vnames

        return self._render(btc)


class CustomFieldsBrick(Brick):
    id_           = Brick.generate_id('creme_config', 'custom_fields')
    dependencies  = (CustomField,)
    verbose_name  = 'Configuration of custom fields'
    template_name = 'creme_config/bricks/custom-fields.html'
    permission    = None  # NB: used by the view creme_core.views.bricks.reload_basic
    configurable  = False

    def detailview_display(self, context):
        # NB: we wrap the ContentType instances instead of store extra data in
        #     them because the instances are stored in a global cache, so we do
        #     not want to mutate them.
        class _ContentTypeWrapper:
            __slots__ = ('ctype', 'cfields')

            def __init__(self, ctype, cfields):
                self.ctype = ctype
                self.cfields = cfields

        cfields = CustomField.objects.all()

        # Retrieve & cache Enum values (in order to display them of course)
        enums_types = {CustomField.ENUM, CustomField.MULTI_ENUM}
        enums_cfields = [cfield
                            for cfield in cfields
                                if cfield.field_type in enums_types
                        ]
        evalues_map = defaultdict(list)

        for enum_value in CustomFieldEnumValue.objects.filter(custom_field__in=enums_cfields):
            evalues_map[enum_value.custom_field_id].append(enum_value.value)

        for enums_cfield in enums_cfields:
            enums_cfield.enum_values = evalues_map[enums_cfield.id]
        # ------

        cfields_per_ct_id = defaultdict(list)
        for cfield in cfields:
            cfields_per_ct_id[cfield.content_type_id].append(cfield)

        get_ct = ContentType.objects.get_for_id
        ctypes = [_ContentTypeWrapper(get_ct(ct_id), ct_cfields)
                    for ct_id, ct_cfields in cfields_per_ct_id.items()
                 ]

        return self._render(self.get_template_context(
                        context, ctypes=ctypes,
        ))


class UsersBrick(_ConfigAdminBrick):
    id_           = _ConfigAdminBrick.generate_id('creme_config', 'users')
    dependencies  = (User,)
    order_by      = 'username'
    verbose_name  = 'Users configuration'
    template_name = 'creme_config/bricks/users.html'

    def detailview_display(self, context):
        users = User.objects.filter(is_team=False)

        if not context['user'].is_staff:
            users = users.exclude(is_staff=True)

        hide_inactive = BricksManager.get(context).get_state(self.id_, context['user']) \
                        .get_extra_data(BRICK_STATE_HIDE_INACTIVE_USERS)
        if hide_inactive:
            users = users.exclude(is_active=False)

        btc = self.get_template_context(context, users, hide_inactive=hide_inactive)
        page = btc['page']
        page_users = page.object_list
        TIME_ZONE = settings.TIME_ZONE
        btc['display_tz'] = (any(user.time_zone != TIME_ZONE for user in page_users)
                             # All users are displayed if our page
                             if page.paginator.count == len(page_users) else
                             User.objects.exclude(time_zone=TIME_ZONE).exists()
                            )

        return self._render(btc)


class TeamsBrick(_ConfigAdminBrick):
    id_           = _ConfigAdminBrick.generate_id('creme_config', 'teams')
    dependencies  = (User,)
    order_by      = 'username'
    verbose_name  = 'Teams configuration'
    template_name = 'creme_config/bricks/teams.html'

    def detailview_display(self, context):
        return self._render(self.get_template_context(
                    context, User.objects.filter(is_team=True),
        ))


class BrickDetailviewLocationsBrick(PaginatedBrick):
    id_           = PaginatedBrick.generate_id('creme_config', 'blocks_dv_locations')
    dependencies  = (BrickDetailviewLocation,)
    page_size     = _PAGE_SIZE - 1  # '-1' because there is always the line for default config on each page
    verbose_name  = 'Blocks locations on detailviews'
    template_name = 'creme_config/bricks/bricklocations-detailviews.html'
    permission    = None  # NB: used by the view creme_core.views.blocks.reload_basic
    configurable  = False

    brick_registry = brick_registry

    def detailview_display(self, context):
        # NB: we wrap the ContentType instances instead of store extra data in
        #     them because the instances are stored in a global cache, so we do
        #     not want to mutate them.
        class _ContentTypeWrapper:  # TODO: move from here ?
            __slots__ = ('ctype', 'locations_info', 'default_count')

            def __init__(self, ctype):
                self.ctype = ctype
                self.default_count = 0
                self.locations_info = ()  # List of tuples (role_arg, role_label, block_count)
                                          # with role_arg == role.id or 'superuser'

        # TODO: factorise with SearchConfigBlock ?
        # TODO: factorise with CustomBlockConfigItemCreateForm , add a method in block_registry ?
        get_ct = ContentType.objects.get_for_model
        is_invalid = self.brick_registry.is_model_invalid
        ctypes = [_ContentTypeWrapper(get_ct(model))
                      for model in creme_registry.iter_entity_models()
                          if not is_invalid(model)
                 ]

        sort_key = collator.sort_key
        ctypes.sort(key=lambda ctw: sort_key(str(ctw.ctype)))

        btc = self.get_template_context(
            context, ctypes,
            max_conf_count=UserRole.objects.count() + 1,  # NB: '+ 1' is for super-users config.
        )

        ctypes_wrappers = btc['page'].object_list

        brick_counts = defaultdict(lambda: defaultdict(int))  # brick_counts[content_type.id][(role_id, superuser)] -> count
        role_ids = set()

        for bdl in BrickDetailviewLocation.objects \
                                          .filter(content_type__in=[ctw.ctype for ctw in ctypes_wrappers])\
                                          .exclude(zone=BrickDetailviewLocation.HAT):
            if bdl.brick_id:  # Do not count the 'place-holder' (empty block IDs which mean "no-block for this zone")
                role_id = bdl.role_id
                brick_counts[bdl.content_type_id][(role_id, bdl.superuser)] += 1
                role_ids.add(role_id)

        role_names = dict(UserRole.objects.filter(id__in=role_ids).values_list('id', 'name'))
        superusers_label = gettext('Superuser')  # TODO: cached_lazy_gettext

        for ctw in ctypes_wrappers:
            count_per_role = brick_counts[ctw.ctype.id]
            ctw.default_count = count_per_role.pop((None, False), 0)

            ctw.locations_info = locations_info = []
            for (role_id, superuser), block_count in count_per_role.items():
                if superuser:
                    role_arg = 'superuser'
                    role_label = superusers_label
                else:
                    role_arg = role_id
                    role_label = role_names[role_id]

                locations_info.append((role_arg, role_label, block_count))

            locations_info.sort(key=lambda t: sort_key(t[1]))  # Sort by role label

        btc['default_count'] = BrickDetailviewLocation.objects.filter(content_type=None,
                                                                      role=None, superuser=False,
                                                                     ).count()

        return self._render(btc)


class BrickHomeLocationsBrick(_ConfigAdminBrick):
    id_           = _ConfigAdminBrick.generate_id('creme_config', 'blocks_home_locations')
    dependencies  = (BrickHomeLocation,)
    verbose_name  = 'Locations of blocks on the home page.'
    template_name = 'creme_config/bricks/bricklocations-home.html'

    def detailview_display(self, context):
        # return self._render(self.get_template_context(
        #             context,
        #             BrickHomeLocation.objects.all(),
        # ))
        superuser_count = BrickHomeLocation.objects.filter(superuser=True).count()

        btc = self.get_template_context(
            context,
            UserRole.objects.exclude(brickhomelocation=None)
                            .order_by('name')
                            .annotate(bricks_count=Count('brickhomelocation')),
            superuser_count=superuser_count,
            empty_configs={
                'superuser' if superuser else (role or 'default')
                    for role, superuser in BrickHomeLocation.objects
                                                            .filter(brick_id='')
                                                            .values_list('role', 'superuser')
            },
        )

        # NB: lambda => lazy
        btc['get_default_count'] = lambda: BrickHomeLocation.objects.filter(role=None, superuser=False).count()

        paginator = btc['page'].paginator
        btc['show_add_button'] = (
            (UserRole.objects.count() > paginator.count)
            or (superuser_count == 0)
        )

        # NB: the UserRole queryset count does not use the default & superuser configuration
        paginator.count += 1 + min(superuser_count, 1)

        return self._render(btc)


class BrickDefaultMypageLocationsBrick(_ConfigAdminBrick):
    id_           = _ConfigAdminBrick.generate_id('creme_config', 'blocks_default_mypage_locations')
    dependencies  = (BrickMypageLocation,)
    verbose_name  = 'Default blocks locations on "My page"'
    template_name = 'creme_config/bricks/bricklocations-mypage-default.html'

    def detailview_display(self, context):
        return self._render(self.get_template_context(
                    context,
                    BrickMypageLocation.objects.filter(user=None),
        ))


class BrickMypageLocationsBrick(_ConfigAdminBrick):
    id_           = _ConfigAdminBrick.generate_id('creme_config', 'blocks_mypage_locations')
    dependencies  = (BrickMypageLocation,)
    verbose_name  = 'Blocks locations on "My page"'
    template_name = 'creme_config/bricks/bricklocations-mypage-user.html'

    def detailview_display(self, context):
        return self._render(self.get_template_context(
                    context,
                    BrickMypageLocation.objects.filter(user=context['user']),
        ))


class RelationBricksConfigBrick(_ConfigAdminBrick):
    id_           = _ConfigAdminBrick.generate_id('creme_config', 'relation_blocks_config')
    dependencies  = (RelationBrickItem, BrickDetailviewLocation)
    verbose_name  = 'Relation blocks configuration'
    template_name = 'creme_config/bricks/relationbricks-configs.html'
    order_by = 'relation_type__predicate'

    def detailview_display(self, context):
        return self._render(self.get_template_context(
                    context, RelationBrickItem.objects.all(),
        ))


class InstanceBricksConfigBrick(_ConfigAdminBrick):
    id_           = _ConfigAdminBrick.generate_id('creme_config', 'instance_blocks_config')
    # BrickDetailviewLocation/BrickHomeLocation/BrickMypageLocation because
    # they can be deleted if we delete a InstanceBrickConfigItem
    dependencies  = (InstanceBrickConfigItem, BrickDetailviewLocation,
                     BrickHomeLocation, BrickMypageLocation,
                    )
    verbose_name  = 'Instance blocks configuration'
    template_name = 'creme_config/bricks/instancebricks-configs.html'

    def detailview_display(self, context):
        return self._render(self.get_template_context(
                    context, InstanceBrickConfigItem.objects.all(),
        ))


class CustomBricksConfigBrick(PaginatedBrick):
    id_           = _ConfigAdminBrick.generate_id('creme_config', 'custom_blocks_config')
    dependencies  = (CustomBrickConfigItem,)
    verbose_name  = 'Custom blocks configuration'
    template_name = 'creme_config/bricks/custombricks-configs.html'
    page_size    = _PAGE_SIZE
    permission   = None  # The portals can be viewed by all users => reloading can be done by all users too.
    configurable = False

    def detailview_display(self, context):
        # NB: we wrap the ContentType instances instead of store extra data in
        #     them because teh instances are stored in a global cache, so we do
        #     not want to mutate them.
        class _ContentTypeWrapper:  # TODO: move from here ?
            __slots__ = ('ctype', 'items')

            def __init__(self, ctype, items):
                self.ctype = ctype
                self.items = items

        cbi_per_ctid = defaultdict(list)

        for cb_item in CustomBrickConfigItem.objects.order_by('name'):
            cbi_per_ctid[cb_item.content_type_id].append(cb_item)

        get_ct = ContentType.objects.get_for_id
        ctypes = [_ContentTypeWrapper(get_ct(ct_id), cb_items)
                      for ct_id, cb_items in cbi_per_ctid.items()
                 ]

        sort_key = collator.sort_key
        ctypes.sort(key=lambda ctw: sort_key(str(ctw.ctype)))

        return self._render(self.get_template_context(context, ctypes))


class ButtonMenuBrick(Brick):
    id_           = Brick.generate_id('creme_config', 'button_menu')
    dependencies  = (ButtonMenuItem,)
    verbose_name  = 'Button menu configuration'
    template_name = 'creme_config/bricks/button-menu.html'
    permission    = None  # NB: used by the view creme_core.views.blocks.reload_basic()
    configurable  = False

    def detailview_display(self, context):
        buttons_map = defaultdict(list)

        for bmi in ButtonMenuItem.objects.order_by('order'):
            buttons_map[bmi.content_type_id].append(bmi)

        build_verbose_names = lambda bm_items: [str(bmi) for bmi in bm_items if bmi.button_id]
        default_buttons = build_verbose_names(buttons_map.pop(None, ()))

        get_ct = ContentType.objects.get_for_id
        buttons = [(get_ct(ct_id), build_verbose_names(bm_items))
                        for ct_id, bm_items in buttons_map.items()
                  ]
        sort_key = collator.sort_key
        buttons.sort(key=lambda t: sort_key(str(t[0])))

        return self._render(self.get_template_context(
                    context,
                    default_buttons=default_buttons,
                    buttons=buttons,
        ))


class SearchConfigBrick(PaginatedBrick):
    id_           = PaginatedBrick.generate_id('creme_config', 'searchconfig')
    dependencies  = (SearchConfigItem,)
    verbose_name  = 'Search configuration'
    template_name = 'creme_config/bricks/search-config.html'
    order_by      = 'content_type'
    # TODO _ConfigAdminBlock => Mixin
    page_size    = _PAGE_SIZE * 2  # Only one brick
    permission   = None  # NB: used by the view creme_core.views.blocks.reload_basic()
    configurable = False

    def detailview_display(self, context):
        # NB: we wrap the ContentType instances instead of store extra data in
        #     them because teh instances are stored in a global cache, so we do
        #     not want to mutate them.
        class _ContentTypeWrapper: # TODO: move from here ?
            __slots__ = ('ctype', 'sc_items')

            def __init__(self, ctype):
                self.ctype = ctype
                self.sc_items = ()

        ctypes = [_ContentTypeWrapper(ctype) for ctype in creme_entity_content_types()]
        sort_key = collator.sort_key
        ctypes.sort(key=lambda ctw: sort_key(str(ctw.ctype)))

        btc = self.get_template_context(
                context, ctypes,
                # NB: '+ 2' is for default config + super-users config.
                max_conf_count=UserRole.objects.count() + 2,
        )

        ctypes_wrappers = btc['page'].object_list

        sci_map = defaultdict(list)
        for sci in SearchConfigItem.objects \
                                   .filter(content_type__in=[ctw.ctype for ctw in ctypes_wrappers])\
                                   .select_related('role'):
            sci_map[sci.content_type_id].append(sci)

        superusers_label = gettext('Superuser')

        for ctw in ctypes_wrappers:
            ctype = ctw.ctype
            ctw.sc_items = sc_items = sci_map.get(ctype.id) or []
            sc_items.sort(key=lambda sci: sort_key(str(sci.role) if sci.role
                                                   else superusers_label if sci.superuser
                                                   else ''
                                                  )
                         )

            if not sc_items or not sc_items[0].is_default:  # No default config -> we build it
                SearchConfigItem.objects.create(content_type=ctype)

        return self._render(btc)


class HistoryConfigBrick(_ConfigAdminBrick):
    id_           = _ConfigAdminBrick.generate_id('creme_config', 'historyconfig')
    dependencies  = (HistoryConfigItem,)
    verbose_name  = 'History configuration'
    template_name = 'creme_config/bricks/history-config.html'
    order_by      = 'relation_type__predicate'

    def detailview_display(self, context):
        return self._render(self.get_template_context(context, HistoryConfigItem.objects.all()))


class UserRolesBrick(_ConfigAdminBrick):
    id_           = _ConfigAdminBrick.generate_id('creme_config', 'user_roles')
    dependencies  = (UserRole,)
    order_by      = 'name'
    verbose_name  = 'User roles configuration'
    template_name = 'creme_config/bricks/user-roles.html'

    def detailview_display(self, context):
        return self._render(self.get_template_context(context, UserRole.objects.all()))


class UserSettingValuesBrick(Brick):
    id_           = QuerysetBrick.generate_id('creme_config', 'user_setting_values')
    # dependencies  = (User,) ??
    verbose_name  = 'My setting values'
    template_name = 'creme_config//bricks/user-setting-values.html'
    configurable  = False
    permission    = None  # NB: used by the view creme_core.views.blocks.reload_basic ;
                          #     None means 'No special permission required'

    user_setting_key_registry = setting_key.user_setting_key_registry

    def detailview_display(self, context):
        # NB: credentials OK: user can only view his own settings
        settings = context['user'].settings
        sv_info_per_app = defaultdict(list)
        get_app_config = apps.get_app_config
        count = 0

        for skey in self.user_setting_key_registry:
            if skey.hidden:
                continue

            info = {
                'description': skey.description,
                'key_id':      skey.id,
            }

            try:
                info['value'] = settings.as_html(skey)
            except KeyError:
                info['not_set'] = True

            sv_info_per_app[skey.app_label].append(info)
            count += 1

        return self._render(self.get_template_context(
                    context,
                    values_per_app=[
                        (get_app_config(app_label).verbose_name, svalues)
                            for app_label, svalues in sv_info_per_app.items()
                    ],
                    count=count,
        ))
