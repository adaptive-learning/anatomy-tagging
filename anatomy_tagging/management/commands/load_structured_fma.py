# -*- coding: utf-8 -*-
from anatomy_tagging.models import Term, Relation, RelationType
from django.core.management.base import BaseCommand, CommandError
from django.template.defaultfilters import slugify
from optparse import make_option
import json
import yaml


class Command(BaseCommand):
    help = u"""Load relations about structures from prepared FMA file"""

    option_list = BaseCommand.option_list + (
        make_option(
            '--source',
            dest='source'
        ),
    )

    def handle(self, *args, **options):
        if options['source'] is None:
            raise CommandError('The source has to be given.')
        self.load_relations(options['source'])

    def load_relations(self, source):
        with open(source, 'r') as f:
            data = yaml.load(f) if source.endswith('.yaml') else json.load(f)
        result = []
        self.init_terms()
        self.rel_types = {}
        self.traverse_structure_and_collect(data, result)

    def traverse_structure_and_collect(self, data, to_save, visited=None):
        if visited is None:
            visited = set()
            for term in data.values():
                self.traverse_structure_and_collect(term, to_save, visited=visited)
            return
        if data['fmaid'] in visited:
            return
        visited.add(data['fmaid'])
        for follow in set(data.keys()) - {'fmaid', 'taid', 'anatomid', 'name_la', 'name_en', 'name_cs'}:
            inserted = set()
            for child in data.get(follow, []):
                child_id = '{}:{}'.format(child.get('taid'), child.get('fmaid'))
                if child_id in inserted:
                    continue
                inserted.add(child_id)
                self.create_relation(
                    key=follow,
                    term1=self.get_term_from_json(data, create=True),
                    term2=self.get_term_from_json(child, create=True)
                )
            for child in data.get(follow, []):
                self.traverse_structure_and_collect(child, to_save, visited=visited)

    def create_relation(self, key, term1, term2):
        rel_type = self.rel_types.get(key)
        if rel_type is None:
            rel_type, _ = RelationType.objects.get_or_create(
                source='fma',
                identifier=key
            )
            self.rel_types[key] = rel_type
        rel, _ = Relation.objects.get_or_create(
            term1_id=term1['id'],
            term2_id=term2['id'],
            type=rel_type
        )
        return rel

    def get_term_from_json(self, data, create=False):
        return self.get_term(
            name_la=data.get('name_la'),
            name_en=data['name_en'],
            name_cs=None,
            taid=data.get('taid'),
            fmaid=data['fmaid'],
            create=create
        )

    def get_term(self, name_la, name_en, name_cs, taid, fmaid, create=False):
        term = self.terms_by_taid.get(taid)
        if term is None:
            term = self.terms_by_fmaid.get(fmaid)
        else:
            if term.fma_id is None or term.fma_id < 0:
                term.fma_id = fmaid
                term.save()
        if term is None and create:
            term = Term.objects.create(
                slug=slugify(name_en),
                code=taid if taid else '',
                name_la=name_la if name_la else '',
                name_en=name_en if name_en else '',
                name_cs=name_cs if name_cs else '',
                fma_id=fmaid
            )
        return term.to_serializable() if term is not None else None

    def init_terms(self):
        if hasattr(self, 'terms_by_name'):
            return
        terms = Term.objects.prepare_related().all()
        self.terms_by_name = {}
        self.terms_by_taid = {}
        self.terms_by_fmaid = {}
        for t in terms:
            for name in t.name_la.split(';'):
                self.terms_by_name[name.lower()] = t
            for name in t.name_en.split(';'):
                self.terms_by_name[name.lower()] = t
            self.terms_by_taid[t.code] = t
            self.terms_by_fmaid[t.fma_id] = t
