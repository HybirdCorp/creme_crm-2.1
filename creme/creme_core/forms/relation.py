# -*- coding: utf-8 -*-

################################################################################
#    Creme is a free/open-source Customer Relationship Management software
#    Copyright (C) 2009-2010  Hybird
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

from django.db.models import Q
from django.forms import CharField, ValidationError
from django.utils.translation import ugettext_lazy as _, ugettext
from django.contrib.contenttypes.models import ContentType

from creme_core.models import CremeEntity, Relation, RelationType
from creme_core.forms import CremeForm
from creme_core.forms.fields import RelatedEntitiesField
from creme_core.forms.widgets import Label


class RelationCreateForm(CremeForm):
    relations = RelatedEntitiesField(label=_(u'Relations'))

    def __init__(self, subject, user, relations_types=None, *args, **kwargs):
        """
        @param relations_types Sequence of RelationTypes ids to narrow to these types ; or None that means all types compatible with the subject.
        """
        super(RelationCreateForm, self).__init__(*args, **kwargs)
        self.subject = subject
        self.user = user

        if not relations_types:
            relations_types = RelationType.get_compatible_ones(subject.entity_type).values_list('id', flat=True)

        self.fields['relations'].relation_types = relations_types

    @staticmethod
    def _entities2unicode(entities, user): #TODO: move to creme_core.utils ?
        return u', '.join(unicode(entity) if entity.can_view(user) else ugettext(u'Entity #%s (not viewable)') % entity.id
                              for entity in entities
                         )

    def clean(self):
        if self._errors:
            return self.cleaned_data

        cleaned_data = self.cleaned_data
        relations    = cleaned_data['relations']

        if not relations:
            raise ValidationError(ugettext(u'No relation'))

        if len(set(((relation_type_id, entity.id) for relation_type_id, entity in relations))) != len(relations):
            raise ValidationError(ugettext(u'There are duplicates'))

        relation_type_ids = set(entry[0] for entry in relations)

        if RelationType.objects.filter(pk__in=relation_type_ids).count() < len(relation_type_ids):
            raise ValidationError(ugettext(u"Some predicates doesn't not exist"))

        user = self.user
        entities = [entity for rt_id, entity in relations]
        CremeEntity.populate_credentials(entities, user)

        unlinkable = self._entities2unicode((e for e in entities if not e.can_link(user)) , user)
        if unlinkable:
            raise ValidationError(ugettext(u"Some entities are not linkable: %s") % unlinkable)

        # TODO : add validation for relations (check doubles, and existence)
        return cleaned_data

    def save(self):
        create_relation = partial(Relation.objects.create, subject_entity=self.subject, user=self.user)

        for relation_type_id, entity in self.cleaned_data['relations']:
            create_relation(type_id=relation_type_id, object_entity=entity)


class MultiEntitiesRelationCreateForm(RelationCreateForm):
    entities_lbl = CharField(label=_(u"Related entities"), widget=Label())

    def __init__(self, subjects, forbidden_subjects, user, *args, **kwargs):
        subject = subjects[0] if subjects else forbidden_subjects[0]
        super(MultiEntitiesRelationCreateForm, self).__init__(subject=subject, user=user, relations_types=None, *args, **kwargs)
        self.subjects = subjects
        self.user = user

        self.fields['entities_lbl'].initial = self._entities2unicode(subjects, user) if subjects else ugettext(u'NONE !')

        if forbidden_subjects:
            self.fields['bad_entities_lbl'] = CharField(label=ugettext(u"Unlinkable entities"),
                                                        widget=Label,
                                                        initial=self._entities2unicode(forbidden_subjects, user)
                                                       )

    @staticmethod
    def hash_relation(subject_id, rtype_id, object_id):
        return '%s#%s#%s' % (subject_id, rtype_id, object_id)

    def save(self):
        user = self.user
        relations_cdata = self.cleaned_data['relations']
        existing_relations_query = Q()

        for subject in self.subjects:
            for rtype_id, object_entity in relations_cdata:
                existing_relations_query |= Q(type=rtype_id, subject_entity=subject, object_entity=object_entity)

        hash_relation = self.hash_relation
        existing_relations = frozenset(hash_relation(r.subject_entity_id, r.type_id, r.object_entity_id)
                                            for r in Relation.objects.filter(existing_relations_query)
                                      )

        create_relation = Relation.objects.create

        for subject in self.subjects:
            for rtype_id, object_entity in relations_cdata:
                if not hash_relation(subject.id, rtype_id, object_entity.id) in existing_relations:
                    create_relation(user=user,
                                    subject_entity=subject,
                                    type_id=rtype_id,
                                    object_entity=object_entity,
                                   )
