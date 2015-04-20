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

#from django.db import transaction, IntegrityError
from django.db import IntegrityError
from django.db.transaction import atomic

from .models import SimpleBillingAlgo
from .registry import Algo


logger = logging.getLogger(__name__)


class SimpleAlgo(Algo):
#    #We use transaction because the IntegrityError aborts the current transaction on PGSQL
#    @transaction.commit_manually
#    def generate_number(self, organisation, ct, *args, **kwargs):
#        while True:
#            sid = transaction.savepoint()
#            old_conf = max(SimpleBillingAlgo.objects.filter(organisation=organisation, ct=ct),
#                           key=lambda algo: algo.last_number
#                          )
#            conf     = SimpleBillingAlgo(organisation=old_conf.organisation,
#                                         ct=old_conf.ct,
#                                         prefix=old_conf.prefix,
#                                         last_number=old_conf.last_number + 1,
#                                        )
#
#            try:
#                # remember the <unique_together = ("organisation", "last_number", "ct")> in SimpleBillingAlgo.Meta
#                conf.save(force_insert=True)
#            except IntegrityError as e: #problen with the 'unique_together' constraint
#                logger.debug('SimpleAlgo.generate_number() (save new conf): %s', e)
#                transaction.savepoint_rollback(sid)
#                continue
#
#            transaction.savepoint_commit(sid)
#
#            try:
#                # protect against case that must never happen
#                # (eg: this loop is preempted on a server during a long time - yes it's a wacky idea! :) )
#                SimpleBillingAlgo.objects.get(pk=old_conf.id).delete()
#            except SimpleBillingAlgo.DoesNotExist:
#                logger.debug('SimpleAlgo.generate_number() (delete old conf): %s', e)
#                conf.delete()
#                continue
#
#            transaction.commit()
#
#            return conf.prefix + str(conf.last_number)
    def generate_number(self, organisation, ct, *args, **kwargs):
        while True:
            old_conf = max(SimpleBillingAlgo.objects.filter(organisation=organisation, ct=ct),
                           key=lambda algo: algo.last_number
                          )
            conf     = SimpleBillingAlgo(organisation=old_conf.organisation,
                                         ct=old_conf.ct,
                                         prefix=old_conf.prefix,
                                         last_number=old_conf.last_number + 1,
                                        )

            try:
                with atomic():
                    # remember the <unique_together = ("organisation", "last_number", "ct")> in SimpleBillingAlgo.Meta
                    conf.save(force_insert=True)
                    SimpleBillingAlgo.objects.filter(pk=old_conf.id).delete()
            except IntegrityError as e: # Problem with the 'unique_together' constraint
                logger.debug('SimpleAlgo.generate_number() (save new conf): %s', e)
                continue

            return conf.prefix + str(conf.last_number)
