# -*- coding: utf-8 -*-

################################################################################
#    Creme is a free/open-source Customer Relationship Management software
#    Copyright (C) 2009-2017  Hybird
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

from future_builtins import filter, map
from collections import defaultdict
import logging

from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.template.loader import get_template
from django.conf import settings
from django.utils.translation import ugettext_lazy as _, ugettext
from django.contrib.contenttypes.models import ContentType

from ..models import (Relation, RelationBlockItem, CremeEntity,
        InstanceBlockConfigItem, CustomBlockConfigItem, BlockState)


logger = logging.getLogger(__name__)


def list4url(list_):
    "Special url list-to-string function"
    return ','.join(str(i) for i in list_)


def str2list(string):
    "'1,2,3'  -> [1, 2, 3]"
    return [int(i) for i in string.split(',') if i.isdigit()]


class _BlockContext(object):  # TODO: rename to Context ?? (so Context-> TemplateContext)
    def __repr__(self):
        return '<BlockContext>'

    def as_dict(self):
        return {}

    @classmethod
    def from_dict(cls, data):
        instance = cls()

        for k, v in data.iteritems():
            setattr(instance, k, v)

        return instance

    def update(self, template_context):
        """Overload me (see _PaginatedBlockContext, _QuerysetBlockContext)"""
        return False


class Block(object):
    """ A block of information.
    Blocks can be displayed on (see creme_core.templatetags.creme_block):
        - a detailview (and so are related to a CremeEntity),
        - a portal (related to the content types of an app)
        - the homepage - ie the portal of creme_core (related to all the apps).

    A Block can be directly displayed on a page (this is the only solution for
    pages that are not a detailview, a portal or the home). But the better
    solution is to use the configuration system (see creme_core.models.blocks
    & creme_config).

    Reloading after a change (deleting, adding, updating, etc...) in the block
    can be done with ajax if the correct view is set : for this, each block has
    a unique id in a page.

    When you inherit the Block class, you have to define these optionnal methods
    to allow the different possibility of display:

    def detailview_display(self, context):
        return 'VOID BLOCK FOR DETAILVIEW: %s' % self.verbose_name

    def portal_display(self, context, ct_ids):
        return 'VOID BLOCK FOR PORTAL: %s' % self.verbose_name

    def home_display(self, context):
        return 'VOID BLOCK FOR HOME: %s' % self.verbose_name
    """
    id_           = None               # Overload with an unicode object ; use generate_id()
    dependencies  = ()                 # List of the models on which the block depends
                                       #   (ie: generally the block displays these models) ;
                                       #   it also can be the '*' string, which is a wildcard meaning
                                       #   'All models used in the page'.
    relation_type_deps = ()            # List of id of RelationType objects on which the block depends ;
                                       #   only used for Blocks which have 'Relation' in their dependencies
    read_only     = False              # 'True' means : the block never causes a DB change on its dependencies models.
                                       #   ---> so when this is reload (eg: to change the pagination), it does
                                       #   not causes the dependant blocks to be reload (but it is still
                                       #   reload when the dependant blocks are reload of course).
    verbose_name  = 'BLOCK'            # Used in the user configuration
                                       #   (see BlockDetailviewLocation/BlockPortalLocation)
    template_name = 'OVERLOAD_ME.html' # Used to render the block of course
    context_class = _BlockContext      # Store the context in the session.
    configurable  = True               # True: the Block can be add/removed to detailview/portal by
                                       #   configuration (see creme_config)
    target_ctypes = ()                 # Tuple of CremeEntity classes that can have this type of block.
                                       #  Empty tuple means that all types are ok. eg: (Contact, Organisation)
    target_apps = ()                   # Tuple of name of the Apps that can have this Block on their portal.
                                       #   Empty tuple means that all Apps are ok. eg: ('persons',)

    @staticmethod
    def generate_id(app_name, name):  # TODO: rename _generate_id ?
        return u'block_%s-%s' % (app_name, name)

    def _render(self, template_context):
        return get_template(self.template_name).render(template_context)

    def _simple_detailview_display(self, context):
        """Helper method to build a basic detailview_display() method for classes that inherit Block."""
        return self._render(self.get_block_template_context(
                                context,
                                # update_url='/creme_core/blocks/reload/%s/%s/' % (
                                #                     self.id_,
                                #                     context['object'].pk,
                                #                 ),
                                update_url=reverse('creme_core__reload_detailview_blocks',
                                                   args=(self.id_, context['object'].pk),
                                                  ),
                           ))

    def _build_template_context(self, context, block_name, block_context, **extra_kwargs):
        context['block_name'] = block_name
        context['state']      = BlocksManager.get(context).get_state(self.id_, context['user'])
        context.update(extra_kwargs)

        return context

    def get_block_template_context(self, context, update_url='', **extra_kwargs):
        """ Build the block template context.
        @param context Template context (contains 'request' etc...).
        @param url String containing url to reload this block with ajax.
        """
        request = context['request']
        base_url = request.GET.get('base_url', request.path)
        block_name = self.id_
        session = request.session

        try:
            serialized_context = session['blockcontexts_manager'][base_url][block_name]
        except KeyError:
            block_context = self.context_class()
        else:
            block_context = self.context_class.from_dict(serialized_context)

        template_context = self._build_template_context(context, block_name, block_context,
                                                        base_url=base_url,
                                                        update_url=update_url,
                                                        **extra_kwargs
                                                       )

        # assert BlocksManager.get(context).block_is_registered(self) #!! problem with blocks in inner popups
        if not BlocksManager.get(context).block_is_registered(self):
            logger.debug('Not registered block: %s', self.id_)

        if block_context.update(template_context):
            session.setdefault('blockcontexts_manager', {}) \
                   .setdefault(base_url, {}) \
                   [block_name] = block_context.as_dict()

            request.session.modified = True

        return template_context


class SimpleBlock(Block):
     detailview_display = Block._simple_detailview_display


class _PaginatedBlockContext(_BlockContext):
    __slots__ = ('page',)

    def __init__(self):
        self.page = 1

    def __repr__(self):
        return '<PaginatedBlockContext: page=%s>' % self.page

    def as_dict(self):
        return {'page': self.page}

    def update(self, template_context):
        page = template_context['page'].number

        if self.page != page:
            modified = True
            self.page = page
        else:
            modified = False

        return modified


class PaginatedBlock(Block):
    """This king of Block is generally represented by a paginated table.
    Ajax changes management is used to chnage page.
    """
    context_class = _PaginatedBlockContext
    page_size     = settings.BLOCK_SIZE  # Number of items in the page

    def _build_template_context(self, context, block_name, block_context, **extra_kwargs):
        request = context['request']
        objects = extra_kwargs.pop('objects')

        page_index = request.GET.get('%s_page' % block_name)
        if page_index is not None:
            try:
                page_index = int(page_index)
            except ValueError:
                logger.debug('Invalid page number for block %s: %s', block_name, page_index)
                page_index = 1
        else:
            page_index = block_context.page

        paginator = Paginator(objects, self.page_size)

        try:
            page = paginator.page(page_index)
        except (EmptyPage, InvalidPage):
            page = paginator.page(paginator.num_pages)

        return super(PaginatedBlock, self)._build_template_context(context, block_name, block_context,
                                                                   page=page, **extra_kwargs
                                                                  )

    def get_block_template_context(self, context, objects, update_url='', **extra_kwargs):
        """@param objects Set of objects to display in the block."""
        return Block.get_block_template_context(self, context, update_url=update_url, objects=objects, **extra_kwargs)


class _QuerysetBlockContext(_PaginatedBlockContext):
    __slots__ = ('page', '_order_by')

    def __init__(self):
        super(_QuerysetBlockContext, self).__init__()  # *args **kwargs ??
        self._order_by = ''

    def __repr__(self):
        return '<QuerysetBlockContext: page=%s order_by=%s>' % (self.page, self._order_by)

    def as_dict(self):
        d = super(_QuerysetBlockContext, self).as_dict()
        d['_order_by'] = self._order_by

        return d

    def get_order_by(self, order_by):
        _order_by = self._order_by

        if _order_by:
            return _order_by

        return order_by

    def update(self, template_context):
        modified = super(_QuerysetBlockContext, self).update(template_context)
        order_by = template_context['order_by']

        if self._order_by != order_by:
            modified = True
            self._order_by = order_by

        return modified


class QuerysetBlock(PaginatedBlock):
    """In this block, displayed objects are stored in a queryset.
    It allows to order objects by one of its columns (which can change): order
    changes are done with ajax of course.
    """
    context_class = _QuerysetBlockContext
    order_by      = ''  # Default order_by value ; '' means no order_by

    def _build_template_context(self, context, block_name, block_context, **extra_kwargs):
        request = context['request']
        order_by = self.order_by

        if order_by:
            request_order_by = request.GET.get('%s_order' % block_name)

            if request_order_by is not None:
                order_by = request_order_by  # TODO: test if order_by is valid (field name) ????
            else:
                order_by = block_context.get_order_by(order_by)

            extra_kwargs['objects'] = extra_kwargs['objects'].order_by(order_by)

        return super(QuerysetBlock, self)._build_template_context(context, block_name, block_context,
                                                                  order_by=order_by, **extra_kwargs
                                                                 )

    def get_block_template_context(self, context, queryset, update_url='', **extra_kwargs):
        """@param queryset Set of objects to display in the block."""
        return PaginatedBlock.get_block_template_context(self, context,
                                                         objects=queryset,
                                                         update_url=update_url,
                                                         **extra_kwargs
                                                        )


class SpecificRelationsBlock(QuerysetBlock):
    dependencies  = (Relation,)  # NB: (Relation, CremeEntity) but useless
    order_by      = 'type'
    verbose_name  = _(u'Relationships')
    template_name = 'creme_core/templatetags/block_specific_relations.html'

    def __init__(self, relationblock_item):
        "@param relationblock_item Instance of RelationBlockItem"
        super(SpecificRelationsBlock, self).__init__()
        self.id_ = relationblock_item.block_id
        self.config_item = relationblock_item

        rtype = relationblock_item.relation_type
        self.relation_type_deps = (rtype.id,)
        self.verbose_name = ugettext(u'Relationship block: %s') % rtype.predicate

    @staticmethod
    def generate_id(app_name, name):
        return u'specificblock_%s-%s' % (app_name, name)

    @staticmethod
    def id_is_specific(id_):
        return id_.startswith(u'specificblock_')

    def detailview_display(self, context):
        entity = context['object']
        config_item = self.config_item
        relation_type = config_item.relation_type
        btc = self.get_block_template_context(
                    context,
                    entity.relations.filter(type=relation_type)
                                    .select_related('type', 'object_entity'),
                    # update_url='/creme_core/blocks/reload/%s/%s/' % (self.id_, entity.pk),
                    update_url=reverse('creme_core__reload_detailview_blocks',
                                       args=(self.id_, entity.pk),
                                      ),
                    relation_type=relation_type,
                   )
        relations = btc['page'].object_list
        entities_by_ct = defaultdict(list)

        Relation.populate_real_object_entities(relations)  # DB optimisation

        for relation in relations:
            entity = relation.object_entity.get_real_entity()
            entity.srb_relation_cache = relation
            entities_by_ct[entity.entity_type_id].append(entity)

        groups = []  # List of tuples (entities_with_same_ct, headerfilter_items)
        unconfigured_group = []  # Entities that do not have a customised columns setting
        colspan = 1  # Unconfigured_group has one column
        get_ct = ContentType.objects.get_for_id

        for ct_id, entities in entities_by_ct.iteritems():
            cells = config_item.get_cells(get_ct(ct_id))

            if cells:
                groups.append((entities, cells))
                colspan = max(colspan, len(cells))
            else:
                unconfigured_group.extend(entities)

        groups.append((unconfigured_group, None))  # Unconfigured_group must be at the end

        btc['groups'] = groups
        btc['colspan'] = colspan + 1 # Add one because of 'Unlink' column

        return self._render(btc)


class CustomBlock(Block):
    """Block that can be customised by the user to display informations of an entity.
    It can display regular, custom & function fields, relationships... (see HeaderFilter & EntityCells)
    """
    template_name = 'creme_core/templatetags/block_custom.html'

    def __init__(self, id_, customblock_conf_item):
        "@param customblock_conf_item Instance of CustomBlockConfigItem"
        super(CustomBlock, self).__init__()
        self.id_ = id_
        self.dependencies = (customblock_conf_item.content_type.model_class(),)  # TODO: other model (FK, M2M, Relation)
        # self.relation_type_deps = () #TODO: if cell is EntityCellRelation
        self.verbose_name = customblock_conf_item.name
        self.config_item = customblock_conf_item

    def detailview_display(self, context):
        entity = context['object']

        return self._render(self.get_block_template_context(
                    context,
                    # update_url='/creme_core/blocks/reload/%s/%s/' % (self.id_, entity.pk),
                    update_url=reverse('creme_core__reload_detailview_blocks',
                                       args=(self.id_, entity.pk),
                                      ),
                    config_item=self.config_item,
        ))


class BlocksManager(object):
    """Using to solve the blocks dependencies problem in a page.
    Blocks can depends on the same model : updating one block involves to update
    the blocks that depends on the same than it.
    """
    var_name = 'blocks_manager'

    class Error(Exception):
        pass

    def __init__(self):
        self._blocks = []
        self._dependencies_map = None
        self._blocks_groups = defaultdict(list)
        self._used_relationtypes = None
        self._state_cache = None

    def add_group(self, group_name, *blocks):
        if self._dependencies_map is not None:
            raise BlocksManager.Error("Can't add block to manager after dependence resolution is done.")

        group = self._blocks_groups[group_name]
        if group:
            raise BlocksManager.Error("This block's group name already exists: %s" % group_name)

        self._blocks.extend(blocks)
        group.extend(blocks)

    def block_is_registered(self, block):
        block_id = block.id_
        return any(b.id_ == block_id for b in self._blocks)

    def _build_dependencies_map(self):
        dep_map = self._dependencies_map

        if dep_map is None:
            self._dependencies_map = dep_map = defaultdict(list)
            wilcarded_blocks = []

            for block in self._blocks:
                dependencies = block.dependencies

                if dependencies == '*':
                    wilcarded_blocks.append(block)
                else:
                    for dep in dependencies:
                        dep_map[dep].append(block)

            if wilcarded_blocks:
                for dep_blocks in dep_map.itervalues():
                    dep_blocks.extend(wilcarded_blocks)

        return dep_map

    def _get_dependencies_ids(self, block):
        dep_map = self._build_dependencies_map()
        depblocks_ids = set()

        if not block.read_only:
            id_ = block.id_

            dependencies = block.dependencies
            if dependencies == '*':
                dependencies = dep_map.keys()

            for dep in dependencies:
                for other_block in dep_map[dep]:
                    if other_block.id_ == id_:
                        continue

                    if dep == Relation:
                        if other_block.dependencies != '*' and \
                           not set(block.relation_type_deps) & set(other_block.relation_type_deps):
                            continue

                    depblocks_ids.add(other_block.id_)

        return depblocks_ids

    @staticmethod
    def get(context):
        return context[BlocksManager.var_name]  # Will raise exception if not created: OK

    def get_remaining_groups(self):
        return self._blocks_groups.keys()

    def get_dependencies_map(self):
        get_dep = self._get_dependencies_ids
        return {block.id_: get_dep(block) for block in self._blocks}

    def get_state(self, block_id, user):
        "Get the state for a block and fill a cache to avoid multiple requests"
        _state_cache = self._state_cache
        if not _state_cache:
            _state_cache = self._state_cache = BlockState.get_for_block_ids([block.id_ for block in self._blocks], user)

        state = _state_cache.get(block_id)
        if state is None:
            state = self._state_cache[block_id] = BlockState.get_for_block_id(block_id, user)
            logger.debug("State not set in cache for '%s'" % block_id)

        return state

    def pop_group(self, group_name):
        return self._blocks_groups.pop(group_name)

    @property
    def used_relationtypes_ids(self):
        if self._used_relationtypes is None:
            self._used_relationtypes = {rt_id for block in self._build_dependencies_map()[Relation]
                                            for rt_id in block.relation_type_deps
                                       }

        return self._used_relationtypes

    @used_relationtypes_ids.setter
    def used_relationtypes_ids(self, relationtypes_ids):
        "@param relation_type_deps Sequence of RelationType objects' ids"
        self._used_relationtypes = set(relationtypes_ids)


class _BlockRegistry(object):
    """Use to retrieve a Block by its id.
    All Blocks should be registered in.
    """
    class RegistrationError(Exception):
        pass

    def __init__(self):
        self._blocks = {}
        self._object_blocks = {}
        self._instance_block_classes = {}
        self._invalid_models = set()

    def register(self, *blocks):
        setdefault = self._blocks.setdefault

        for block in blocks:
            if setdefault(block.id_, block) is not block:
                raise _BlockRegistry.RegistrationError("Duplicated block's id: %s" % block.id_)

    def register_4_instance(self, *block_classes):  # TODO: factorise
        setdefault = self._instance_block_classes.setdefault

        for block_class in block_classes:
            if setdefault(block_class.id_, block_class) is not block_class:
                raise _BlockRegistry.RegistrationError("Duplicated block's id: %s" % block_class.id_)

    def register_invalid_models(self, *models):
        """Register some models which cannot have a blocks configuration for
        their detailviews (eg: they have no detailview, or they are not 'classical' ones).
        @param models Classes inheriting CremeEntity.
        """
        add = self._invalid_models.add

        for model in models:
            assert issubclass(model, CremeEntity)
            add(model)

    def register_4_model(self, model, block):  # TODO: had an 'overload' arg ??
        block.id_ = self._generate_modelblock_id(model)

        if not block.dependencies:
            block.dependencies  = (model,)

        # NB: the key is the class, not the ContentType.id because it can cause
        # some inconsistencies in DB problem in unit tests (contenttypes cache bug with tests ??)
        self._object_blocks[model] = block

    def _generate_modelblock_id(self, model):
        meta = model._meta
        return u'modelblock_%s-%s' % (meta.app_label, meta.model_name)

    def __getitem__(self, block_id):
        return self._blocks[block_id]

    def __iter__(self):
        return self._blocks.iteritems()

    def get_block_4_instance(self, ibi, entity=None):
        """Get a Block instance corresponding to a InstanceBlockConfigItem.
        @param ibi InstanceBlockConfigItem instance.
        @param entity CremeEntity instance if your Block has to be displayed on its detailview.
        @return Block instance.
        """
        block_id = ibi.block_id
        block_class = self._instance_block_classes.get(InstanceBlockConfigItem.get_base_id(block_id))

        if block_class is None:
            logger.warning('Block class seems deprecated: %s', block_id)

            block = Block()
            block.verbose_name = '??'
            block.errors = [_('Unknow type of block (bad uninstall ?)')]
        else:
            block = block_class(ibi)
            block.id_ = block_id
            #block.verbose_name = ugettext(u"Block of instance: %s") % ibi

            if entity:
                # When an InstanceBlock is on a detailview of a entity, the content
                # of this blockdepends (generally) of this entity, so we have to
                # complete the dependencies.
                model = entity.__class__
                if model not in block.dependencies:
                    block.dependencies += (model,)

        return block

    def get_blocks(self, block_ids, entity=None):
        """Blocks type can be SpecificRelationsBlock/InstanceBlockConfigItem:
        in this case,they are not really registered, but created on the fly.
        @param block_ids Sequence of id of blocks
        @param entity If given, the dependencies are better computed when the
                      blocks are displayed of the detailview of this entity.
        """
        specific_ids = list(filter(SpecificRelationsBlock.id_is_specific, block_ids))
        instance_ids = list(filter(InstanceBlockConfigItem.id_is_specific, block_ids))
        custom_ids   = list(filter(None, map(CustomBlockConfigItem.id_from_block_id, block_ids)))

        relation_blocks_items = {rbi.block_id: rbi
                                    for rbi in RelationBlockItem.objects.filter(block_id__in=specific_ids)
                                } if specific_ids else {}
        instance_blocks_items = {ibi.block_id: ibi
                                    for ibi in InstanceBlockConfigItem.objects.filter(block_id__in=instance_ids)
                                } if instance_ids else {}
        custom_blocks_items = {cbci.generate_id(): cbci
                                    for cbci in CustomBlockConfigItem.objects.filter(id__in=custom_ids)
                              } if custom_ids else {}

        blocks = []

        for id_ in block_ids:
            rbi = relation_blocks_items.get(id_)
            ibi = instance_blocks_items.get(id_)  # TODO: do only if needed....
            cbci = custom_blocks_items.get(id_)  # TODO: idem

            if rbi:
                block = SpecificRelationsBlock(rbi)
            elif ibi:
                block = self.get_block_4_instance(ibi, entity)
            elif cbci:
                block = CustomBlock(id_, cbci)
            elif id_.startswith('modelblock_'):  # TODO: constant ?
                block = self.get_block_4_object(ContentType.objects
                                                           .get_by_natural_key(*id_[len('modelblock_'):].split('-'))
                                               )
            else:
                block = self._blocks.get(id_)

                if block is None:
                    logger.warning('Block seems deprecated: %s', id_)
                    block = Block()

            blocks.append(block)

        return blocks

    def get_block_4_object(self, obj_or_ct):
        """Return the Block that displays fields for a CremeEntity instance.
        @param obj_or_ct Model (class inheriting CremeEntity), or ContentType instance
                         representing this model, or instance of this model.
        """
        model = obj_or_ct.__class__ if isinstance(obj_or_ct, CremeEntity) else \
                obj_or_ct.model_class() if isinstance(obj_or_ct, ContentType) else \
                obj_or_ct
        block = self._object_blocks.get(model)

        if not block:
            block = SimpleBlock()
            block.id_ = self._generate_modelblock_id(model)
            block.dependencies = (model,)
            block.template_name = 'creme_core/templatetags/block_object.html'

            self._object_blocks[model] = block

        return block

    def get_compatible_blocks(self, model=None):
        """Returns the list of registered blocks that are configurable and compatible with the given ContentType.
        @param model Constraint on a CremeEntity class ;
                     None means blocks must be compatible with all kind of CremeEntity.
        """
        for block in self._blocks.itervalues():
            if block.configurable and hasattr(block, 'detailview_display') \
               and (not block.target_ctypes or model in block.target_ctypes):
                yield block

        # TODO: filter compatible relation types (but the constraints can change after we config blocks...)
        for rbi in RelationBlockItem.objects.all():  # TODO: select_related('relation_type') ??
            yield SpecificRelationsBlock(rbi)

        for ibi in InstanceBlockConfigItem.objects.all():
            block = self.get_block_4_instance(ibi)

            if hasattr(block, 'detailview_display') \
               and (not block.target_ctypes or model in block.target_ctypes):
                yield block

        if model:
            for cbci in CustomBlockConfigItem.objects.filter(content_type=ContentType.objects.get_for_model(model)):
                yield CustomBlock(cbci.generate_id(), cbci)

    def get_compatible_portal_blocks(self, app_name):
        method_name = 'home_display' if app_name == 'creme_core' else 'portal_display'

        for block in self._blocks.itervalues():
            if block.configurable and hasattr(block, method_name) \
               and (not block.target_apps or app_name in block.target_apps):
                yield block

        for ibi in InstanceBlockConfigItem.objects.all():
            block = self.get_block_4_instance(ibi)

            if hasattr(block, method_name) and \
               (not block.target_apps or app_name in block.target_apps):
                yield block

    def is_model_invalid(self, model):
        "See register_invalid_model"
        return model in self._invalid_models


block_registry = _BlockRegistry()
