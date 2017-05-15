# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from collections import defaultdict, deque
from django.db import migrations
import json as simplejson

"""
HACK: This is an ugly hack, because we have no access to the methods of model
managers. Since this is only one-time migration I do not bother refactoring the
code.
"""


def from_identifier(self, identifier, source=None):
    if source is not None:
        return self.get_or_create(identifier=identifier, source=source)[0]
    else:
        found = list(self.filter(identifier=identifier))
        if len(found) == 0:
            raise Exception('There is no relation type of the given identifier {}.'.format(identifier))
        elif len(found) > 1:
            raise Exception('There are multiple relation types of the given identifier {}.'.format(identifier))
        return found[0]


def prepare_related(self):
    return self.select_related('term1', 'term2', 'term1__parent', 'term2__parent', 'type')


def get_graph(self, relation_types, states=None):
    rtype_ids = {relation_type.pk for relation_type in relation_types} | {t.pk for relation_type in relation_types for t in relation_type.synonyms.all()}
    by_id = {}
    by_term1 = defaultdict(list)
    for relation in self.filter(type_id__in=rtype_ids):
        by_id[relation.pk] = to_serializable(relation)
        if relation.term1_id is not None:
            by_term1[relation.term1_id].append(relation.pk)
        else:
            by_term1[relation.text1].append(relation.pk)
    for rel_id, rel_data in by_id.items():
        if rel_data['term2'] is None:
            children = by_term1[rel_data['text2']]
        else:
            children = by_term1[rel_data['term2']['id']]
        rel_data['children'] = children
        for child_id in children:
            child = by_id[child_id]
            if 'parent_ids' in child:
                child['parent_ids'].append(rel_id)
            else:
                child['parent_ids'] = [rel_id]
    previous = None
    previous_to_process = None
    next_to_process = None
    next_ = None
    result_by_id = {}
    for rel_id, rel_data in sorted(by_id.items(), key=lambda x: (x[1]['term1']['name_la'], x[1]['term1']['name_en'])):
        if 'parent_ids' in rel_data:
            continue
        to_visit = deque([rel_id])
        while len(to_visit) > 0:
            current = by_id[to_visit.popleft()]
            if states is not None and current['state'] not in states:
                continue
            if 'next' in current:
                continue
            result_by_id[current['id']] = current
            if next_ is None:
                next_ = current['id']
            if current['state'] == 'unknown':
                if previous_to_process is not None:
                    previous_to_process['next_to_process'] = current['id']
                else:
                    next_to_process = current['id']
                previous_to_process = current
            if previous is not None:
                current['previous'] = previous['id']
                previous['next'] = current['id']
            for child_id in current.get('children', []):
                to_visit.append(child_id)
            previous = current
    return result_by_id, next_, next_to_process


def to_serializable(self):
    STATES = {
        'u': 'unknown',
        'v': 'valid',
        'i': 'invalid',
    }
    obj = {
        'id': self.id,
        'name': self.type.identifier,
        'term1': to_serializable_or_none(self.term1),
        'term2': to_serializable_or_none(self.term2),
        'text1': self.text1,
        'text2': self.text2,
        'state': STATES[self.state],
    }
    if self.labels:
        obj['labels'] = sorted(self.labels.split('|'))
    return obj


def to_serializable_or_none(obj, **kwargs):
    def _to_serializable(self):
        return {
            'id': self.id,
            'code': self.code if self.code != "" else self.slug,
            'slug': self.slug,
            'name_la': self.name_la,
            'name_cs': self.name_cs,
            'name_en': self.name_en,
            'body_part': self.body_part,
            'system': self.system,
            'fma_id': self.fma_id,
        }
    return _to_serializable(obj, **kwargs) if obj is not None else None

"""
END OF HACK
"""

def is_term_artery(term):
    if 'artery' in term.name_en:
        return True
    if 'arteria' in term.name_la:
        return True
    if term.code and term.code.startswith('A12'):
        return True
    return False


def split_branch_relation(apps, schema_editor):
    Relation = apps.get_model("anatomy_tagging", "Relation")
    RelationType = apps.get_model("anatomy_tagging", "RelationType")
    branch = RelationType.objects.get(identifier='branch')
    branch_artery = from_identifier(RelationType.objects, identifier='branch_artery', source='fma')
    branch_nerve = from_identifier(RelationType.objects, identifier='branch_nerve', source='fma')
    rtypes = {branch} | {t for t in branch.synonyms.all()}
    relations = {r.pk: r for r in prepare_related(Relation.objects.filter(type__in=rtypes))}
    graph, next_, next_to_process = get_graph(Relation.objects, rtypes)
    is_artery = {}
    rnext = next_
    while rnext is not None:
        r = relations[rnext]
        parent_is_artery = any([is_artery.get(p, False) for p in graph[rnext].get('parent_ids', [])])
        if parent_is_artery or is_term_artery(r.term1) or is_term_artery(r.term2):
            is_artery[rnext] = True
        rnext = graph[rnext].get('next')
    for r in relations.values():
        if is_artery.get(r.id, False):
            r.type = branch_artery
        else:
            r.type = branch_nerve
        r.save()
    branch.delete()


def merge_branch_relations(apps, schema_editor):
    Relation = apps.get_model("anatomy_tagging", "Relation")
    RelationType = apps.get_model("anatomy_tagging", "RelationType")
    branch = from_identifier(RelationType.objects, identifier='branch', source='fma')
    branch_artery = RelationType.objects.get(identifier='branch_artery')
    branch_nerve = RelationType.objects.get(identifier='branch_nerve')
    for r in Relation.objects.filter(type__identifier__in=['branch_artery', 'branch_nerve']):
        r.type = branch
        r.save()
    branch_artery.delete()
    branch_nerve.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('anatomy_tagging', '0019_auto_constraints'),
    ]

    operations = [
        migrations.RunPython(split_branch_relation, reverse_code=merge_branch_relations),
    ]
