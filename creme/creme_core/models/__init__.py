# -*- coding: utf-8 -*-

from .auth import CremeUser, EntityCredentials, UserRole, SetCredentials #, UserProfile, TeamM2M

from .base import CremeModel, CremeAbstractEntity#, CremeEntityManager
from .entity import CremeEntity

from .setting_value import SettingValue

from .relation import RelationType, Relation, SemiFixedRelationType
from .creme_property import CremePropertyType, CremeProperty
from .custom_field import *

from .fields_config import FieldsConfig
from .header_filter import HeaderFilter
from .entity_filter import EntityFilter, EntityFilterCondition, EntityFilterVariable

from .lock import Mutex, MutexAutoLock

from .i18n import Language
from .currency import Currency
from .vat import Vat

from .block import *
from .prefered_menu import PreferedMenuItem
from .button_menu import ButtonMenuItem

from .reminder import DateReminder

from .history import HistoryLine, HistoryConfigItem
from .search import SearchConfigItem

from .version import Version


from django.conf import settings
if settings.TESTS_ON:
    from creme.creme_core.tests.fake_models import *
