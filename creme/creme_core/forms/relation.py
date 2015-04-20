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

from django.db.models import Q
from django.forms import CharField, ModelMultipleChoiceField, ValidationError
from django.utils.translation import ugettext_lazy as _, ugettext

from ..models import Relation, RelationType, SemiFixedRelationType #CremeEntity
from ..utils import entities2unicode
from .base import CremeForm, FieldBlockManager
from .fields import MultiRelationEntityField
from .validators import validate_linkable_entities
from .widgets import Label, UnorderedMultipleChoiceWidget


class _RelationsCreateForm(CremeForm):
    relations        = MultiRelationEntityField(label=_(u'Relationships'), required=False, autocomplete=True)
    semifixed_rtypes = ModelMultipleChoiceField(label=_(u'Semi-fixed types of relationship'),
                                                queryset=SemiFixedRelationType.objects.none(),
                                                required=False, widget=UnorderedMultipleChoiceWidget
                                               )

    error_messages = {
        'duplicates': _(u'There are duplicates: %(duplicates)s'),
        'link_themselves': _(u'An entity can not be linked to itself : %(entities)s'),
        'empty': _(u'You must give one relationship at least.'),
    }

    def __init__(self, subjects, content_type, relations_types=None, *args, **kwargs):
        """Constructor.
        @param subjects CremeEntity instances that will be the subjects of Relations.
        @param content_type Type of the sujects
        @param relations_types Sequence of RelationTypes ids to narrow to these types ;
                               or None that means all types compatible with the parameter 'content_type'.
        """
        super(_RelationsCreateForm, self).__init__(*args, **kwargs)
        self.subjects = subjects
        self.subjects_ids = subjects_ids = frozenset(s.id for s in subjects)

        fields = self.fields
        #TODO: improve queries ??
        user = self.user
        entities = [sfrt.object_entity 
                        for sfrt in SemiFixedRelationType.objects
                                                         .exclude(object_entity__in=subjects_ids)
                                                         .select_related('object_entity')
                   ]
        sfrt_queryset = SemiFixedRelationType.objects.filter(object_entity__in=filter(user.has_perm_to_link, entities))

        if not relations_types:
            relations_types = RelationType.get_compatible_ones(content_type)
        else:
            sfrt_queryset = sfrt_queryset.filter(relation_type__in=relations_types)

        fields['semifixed_rtypes'].queryset = sfrt_queryset

        #TODO: add a qfilter to exclude the subjects from possible objects
        relations_field = fields['relations']
        relations_field.allowed_rtypes = relations_types
        relations_field.initial = [(relations_field.allowed_rtypes.all()[0], None)]

    def _check_duplicates(self, relations, user):
        future_relations = set()
        duplicates = []

        for rtype, entity in relations:
            r_id = '%s#%s' % (rtype.id, entity.id)

            if r_id in future_relations:
                duplicates.append((rtype, entity))
            else:
                future_relations.add(r_id)

        if duplicates:
            raise ValidationError(self.error_messages['duplicates'],
                                  params={'duplicates': 
                                              u', '.join(u'(%s, %s)' % (rtype, e.allowed_unicode(user))
                                                            for rtype, e in duplicates
                                                        ),
                                         },
                                  code='duplicates',
                                 )

    def _check_loops(self, relations):
        subjects_ids = self.subjects_ids
        bad_objects = [unicode(entity) for rtype, entity in relations if entity.id in subjects_ids]

        if bad_objects:
            raise ValidationError(self.error_messages['link_themselves'],
                                  params={'entities': u', '.join(bad_objects)},
                                  code='link_themselves',
                                 )

    def clean_relations(self):
        relations = self.cleaned_data['relations']
        user = self.user

        self._check_duplicates(relations, user)
        self._check_loops(relations)
        validate_linkable_entities([entity for rt_id, entity in relations], user)

        return relations

    def clean(self):
        cdata = super(_RelationsCreateForm, self).clean()

        if not self._errors:
            relations_desc = cdata['relations']
            #TODO: improve queries ??
            relations_desc.extend((sfrt.relation_type, sfrt.object_entity) for sfrt in cdata['semifixed_rtypes'])

            if not relations_desc:
                raise ValidationError(self.error_messages['empty'], code='empty')

            self._check_duplicates(relations_desc, self.user)

            self.relations_desc = relations_desc

        return cdata

    @staticmethod
    def _hash_relation(subject_id, rtype_id, object_id):
        return '%s#%s#%s' % (subject_id, rtype_id, object_id)

    def save(self):
        user = self.user
        subjects = self.subjects
        hash_relation = self._hash_relation
        relations_desc = self.relations_desc
        existing_relations_query = Q()

        for subject in subjects:
            for rtype, object_entity in relations_desc:
                existing_relations_query |= Q(type=rtype, subject_entity=subject.id, object_entity=object_entity.id)

        existing_relations = frozenset(hash_relation(r.subject_entity_id, r.type_id, r.object_entity_id)
                                            for r in Relation.objects.filter(existing_relations_query)
                                      )
        create_relation = Relation.objects.create

        for subject in subjects:
            for rtype, object_entity in relations_desc:
                if not hash_relation(subject.id, rtype.id, object_entity.id) in existing_relations:
                    create_relation(user=user,
                                    subject_entity=subject,
                                    type=rtype,
                                    object_entity=object_entity,
                                   )

class RelationCreateForm(_RelationsCreateForm):
    def __init__(self, subject, relations_types=None, *args, **kwargs):
        super(RelationCreateForm, self).__init__([subject], subject.entity_type,
                                                 relations_types=relations_types,
                                                 *args, **kwargs
                                                )


class MultiEntitiesRelationCreateForm(_RelationsCreateForm):
    entities_lbl = CharField(label=_(u"Related entities"), widget=Label())

    #TODO: use Meta.fields ?? (beware to bad_entities_lbl)
    blocks = FieldBlockManager(('general', _(u'General information'), ['entities_lbl', 'relations', 'semifixed_rtypes']),)

    def __init__(self, subjects, forbidden_subjects, relations_types=None, *args, **kwargs):
        first_subject = subjects[0] if subjects else forbidden_subjects[0]
        super(MultiEntitiesRelationCreateForm, self).__init__(subjects, first_subject.entity_type,
                                                              relations_types=relations_types,
                                                              *args, **kwargs
                                                             )

        user = self.user
        fields = self.fields
        fields['entities_lbl'].initial = entities2unicode(subjects, user) if subjects else ugettext(u'NONE !')

        if forbidden_subjects:
            fields['bad_entities_lbl'] = CharField(label=ugettext(u"Unlinkable entities"),
                                                   widget=Label,
                                                   initial=entities2unicode(forbidden_subjects, user),
                                                  )
