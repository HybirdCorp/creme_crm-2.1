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

from functools import partial
import logging

from django.core.exceptions import ValidationError
from django.db.models import (CharField, DecimalField, BooleanField, TextField,
        PositiveIntegerField, ForeignKey, PROTECT)
from django.utils.translation import ugettext_lazy as _, ugettext

from creme.creme_core.models import CremeEntity, Relation, Vat

from ..constants import (REL_OBJ_HAS_LINE, REL_SUB_LINE_RELATED_ITEM, PERCENT_PK,
        DISCOUNT_UNIT, DEFAULT_DECIMAL, DEFAULT_QUANTITY)
from ..utils import round_to_2


logger = logging.getLogger(__name__)


# TODO: use a smart workflow engine to update the BillingModel only once when several lines are edited
#       for the moment when have to re-save the model manually.

class Line(CremeEntity):
    # NB: not blank (no related item => name is filled)
    on_the_fly_item = CharField(_(u'On-the-fly line'), max_length=100, null=True)

    comment         = TextField(_('Comment'), blank=True, null=True)
    quantity        = DecimalField(_(u'Quantity'), max_digits=10, decimal_places=2, default=DEFAULT_QUANTITY)
    unit_price      = DecimalField(_(u'Unit price'), max_digits=10, decimal_places=2, default=DEFAULT_DECIMAL)
    unit            = CharField(_(u'Unit'), max_length=100, blank=True)
    discount        = DecimalField(_(u'Discount'), max_digits=10, decimal_places=2, default=DEFAULT_DECIMAL)
    # TODO: remove total_discount & add a choice to discount_unit (see EditForm)
    # TODO: null=False ???
    discount_unit   = PositiveIntegerField(_(u'Discount Unit'), blank=True, null=True, editable=False,
                                           choices=DISCOUNT_UNIT.items(), default=PERCENT_PK,
                                          )
    total_discount  = BooleanField(_('Total discount ?'), editable=False, default=False)
    vat_value       = ForeignKey(Vat, verbose_name=_(u'VAT'), blank=True, null=True, on_delete=PROTECT)  # TODO null=False

    creation_label = _('Add a line')

    _related_document = False
    _related_item = None

    class Meta:
        abstract = True
        app_label = 'billing'
        verbose_name = _(u'Line')
        verbose_name_plural = _(u'Lines')
        ordering = ('created',)

    def _pre_delete(self):
        for relation in Relation.objects.filter(type__in=[REL_OBJ_HAS_LINE, REL_SUB_LINE_RELATED_ITEM],
                                                subject_entity=self.id,
                                               ):
            relation._delete_without_transaction()

    def _pre_save_clone(self, source):
        self.related_document = source._new_related_document
        self.related_item     = source.related_item

    def clean(self):
        if self.discount_unit == PERCENT_PK:
            if not (0 <= self.discount <= 100):
                raise ValidationError(ugettext(u"If you choose % for your discount unit, "
                                               u"your discount must be between 1 and 100%"
                                              ),
                                      code='invalid_percentage',
                                     )
        elif self.total_discount:  # Global discount
            if self.discount > self.unit_price * self.quantity:
                raise ValidationError(ugettext(u"Your overall discount is superior than"
                                               u" the total line (unit price * quantity)"
                                              ),
                                      code='discount_gt_total',
                                     )
        else:  # Unitary discount
            if self.discount > self.unit_price:
                raise ValidationError(ugettext(u"Your discount is superior than the unit price"),
                                      code='discount_gt_unitprice',
                                     )

        if self.related_item:
            if self.on_the_fly_item:
                raise ValidationError(ugettext(u"You cannot set an on the fly name "
                                               u"to a line with a related item"
                                              ),
                                      code='useless_name',
                                     )
        elif not self.on_the_fly_item:
            raise ValidationError(ugettext(u"You must define a name for an on the fly item"),
                                  code='required_name',
                                 )

        super(Line, self).clean()

    def clone(self, new_related_document=None):
        # BEWARE: CremeProperty and Relation are not cloned (except our 2 internal relations)
        self._new_related_document = new_related_document or self.related_document

        return super(Line, self).clone()

    def get_absolute_url(self):
        return self.get_related_entity().get_absolute_url()

    def get_price_inclusive_of_tax(self, document=None):
        total_ht = self.get_price_exclusive_of_tax(document)
        vat_value = self.vat_value
        vat = (total_ht * vat_value.value / 100) if vat_value else 0
        return round_to_2(total_ht + vat)

    def get_raw_price(self):
        return round_to_2(self.quantity * self.unit_price)

    def get_price_exclusive_of_tax(self, document=None):
        document                = document if document else self.related_document
        discount_document       = document.discount if document else None
        discount_line           = self.discount
        global_discount_line    = self.total_discount
        unit_price_line         = self.unit_price

        if self.discount_unit == PERCENT_PK and discount_line:
            total_after_first_discount = self.quantity * (unit_price_line - (unit_price_line * discount_line / 100 ))
        elif global_discount_line:
            total_after_first_discount = self.quantity * unit_price_line - discount_line
        else:
            total_after_first_discount = self.quantity * (unit_price_line - discount_line)

        total_exclusive_of_tax = total_after_first_discount
        if discount_document:
            total_exclusive_of_tax -= total_after_first_discount * discount_document / 100

        return round_to_2(total_exclusive_of_tax)

    def get_related_entity(self):  # For generic views & delete
        return self.related_document

    @property
    def related_document(self):
        related = self._related_document

        if related is False:
            try:
                related = self.relations.get(type=REL_OBJ_HAS_LINE, subject_entity=self.id) \
                                        .object_entity \
                                        .get_real_entity()
            except Relation.DoesNotExist:
                related = None

            self._related_document = related

        return related

    @related_document.setter
    def related_document(self, billing_entity):
        assert self.pk is None, 'Line.related_document(setter): line is already saved (can not change any more).'
        self._related_document = billing_entity

    @property
    def related_item(self):
        if self.id and not self._related_item and not self.on_the_fly_item:
            try:
                self._related_item = self.relations.get(type=REL_SUB_LINE_RELATED_ITEM,
                                                        subject_entity=self.id,
                                                       ).object_entity.get_real_entity()
            except Relation.DoesNotExist:
                logger.warn('Line.related_item(): relation does not exist !!')

        return self._related_item

    @related_item.setter
    def related_item(self, entity):
        assert self.pk is None, 'Line.related_item(setter): line is already saved (can not change any more).'
        self._related_item = entity

    def save(self, *args, **kwargs):
        if not self.pk:  # Creation
            assert self._related_document, 'Line.related_document is required'
            assert bool(self._related_item) ^ bool(self.on_the_fly_item), 'Line.related_item or Line.on_the_fly_item is required'

            self.user = self._related_document.user

            super(Line, self).save(*args, **kwargs)

            create_relation = partial(Relation.objects.create, subject_entity=self, user=self.user)
            create_relation(type_id=REL_OBJ_HAS_LINE, object_entity=self._related_document)

            if self._related_item:
                create_relation(type_id=REL_SUB_LINE_RELATED_ITEM, object_entity=self._related_item)
        else:
            super(Line, self).save(*args, **kwargs)

        # TODO: problem, if several lines are added/edited at once, lots of useless queries (workflow engine ??)
        self.related_document.save()  # Update totals
