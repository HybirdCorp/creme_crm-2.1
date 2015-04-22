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

import logging

from django.apps import apps
#from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext as _

from creme.creme_core.blocks import properties_block, relations_block, customfields_block, history_block
from creme.creme_core.core.entity_cell import EntityCellRegularField
from creme.creme_core.management.commands.creme_populate import BasePopulator
from creme.creme_core.models import RelationType, BlockDetailviewLocation, SearchConfigItem, HeaderFilter
from creme.creme_core.utils import create_if_needed

from . import get_document_model, get_folder_model, folder_model_is_custom
#from .models import Document, FolderCategory, Folder
from .models import FolderCategory
from .blocks import folder_docs_block #linked_docs_block
from .constants import *


logger = logging.getLogger(__name__)


class Populator(BasePopulator):
    dependencies = ['creme_core']

    def populate(self):
        already_populated = RelationType.objects.filter(pk=REL_SUB_RELATED_2_DOC).exists()

        Document = get_document_model()
        Folder   = get_folder_model()

        RelationType.create((REL_SUB_RELATED_2_DOC, _(u'related to the document')),
                            (REL_OBJ_RELATED_2_DOC, _(u'document related to'),      [Document])
                           )


        #TODO: pk string + is_custom=False ??
        entities_cat = create_if_needed(FolderCategory, {'pk': DOCUMENTS_FROM_ENTITIES}, name=unicode(DOCUMENTS_FROM_ENTITIES_NAME))
        create_if_needed(FolderCategory,                {'pk': DOCUMENTS_FROM_EMAILS},   name=unicode(DOCUMENTS_FROM_EMAILS_NAME))

        if not folder_model_is_custom():
            if not Folder.objects.filter(title="Creme").exists(): #TODO: UUID ??
                Folder.objects.create(user=get_user_model().objects.get(pk=1),
                                    title="Creme", category=entities_cat,
                                    description=_(u"Folder containing all the documents related to entities"),
                                    )
            else:
                logger.info("A Folder with title 'Creme' already exists => no re-creation")


        HeaderFilter.create(pk='documents-hf_document', name=_(u"Document view"), model=Document,
                            cells_desc=[(EntityCellRegularField, {'name': 'title'}),
                                        (EntityCellRegularField, {'name': 'folder__title'}),
                                       ]
                                )
        HeaderFilter.create(pk='documents-hf_folder', name=_(u"Folder view"), model=Folder,
                            cells_desc=[(EntityCellRegularField, {'name': 'title'}),
                                        (EntityCellRegularField, {'name': 'description'}),
                                        (EntityCellRegularField, {'name': 'category'}),
                                       ]
                           )


        SearchConfigItem.create_if_needed(Document, ['title', 'description', 'folder__title'])
        SearchConfigItem.create_if_needed(Folder,   ['title', 'description', 'category__name'])


        if not already_populated:
            BlockDetailviewLocation.create_4_model_block(order=5, zone=BlockDetailviewLocation.LEFT, model=Folder)
            BlockDetailviewLocation.create(block_id=customfields_block.id_, order=40,  zone=BlockDetailviewLocation.LEFT,  model=Folder)
            BlockDetailviewLocation.create(block_id=folder_docs_block.id_,  order=50,  zone=BlockDetailviewLocation.LEFT,  model=Folder)
            BlockDetailviewLocation.create(block_id=properties_block.id_,   order=450, zone=BlockDetailviewLocation.LEFT,  model=Folder)
            BlockDetailviewLocation.create(block_id=relations_block.id_,    order=500, zone=BlockDetailviewLocation.LEFT,  model=Folder)
            BlockDetailviewLocation.create(block_id=history_block.id_,      order=20,  zone=BlockDetailviewLocation.RIGHT, model=Folder)

            if apps.is_installed('creme.assistants'):
                logger.info('Assistants app is installed => we use the assistants blocks on detail view')

                from creme.assistants.blocks import alerts_block, memos_block, todos_block, messages_block

                BlockDetailviewLocation.create(block_id=todos_block.id_,    order=100, zone=BlockDetailviewLocation.RIGHT, model=Folder)
                BlockDetailviewLocation.create(block_id=memos_block.id_,    order=200, zone=BlockDetailviewLocation.RIGHT, model=Folder)
                BlockDetailviewLocation.create(block_id=alerts_block.id_,   order=300, zone=BlockDetailviewLocation.RIGHT, model=Folder)
                BlockDetailviewLocation.create(block_id=messages_block.id_, order=400, zone=BlockDetailviewLocation.RIGHT, model=Folder)
