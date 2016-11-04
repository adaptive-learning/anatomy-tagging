# -*- coding: utf-8 -*-
from anatomy_tagging.models import Term
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from optparse import make_option
import copy
import yaml
import os
import json


class Command(BaseCommand):
    help = u"""Load relations about structures from prepared FMA file"""

    FOLLOW = ['branch', 'tributary']

    option_list = BaseCommand.option_list + (
        make_option(
            '--source',
            dest='source'
        ),
        make_option(
            '--dest',
            dest='destination'
        )
    )

    def handle(self, *args, **options):
        if options['source'] is None:
            raise CommandError('The source has to be given.')
        self.get_relations(options['source'], destination=options['destination'], force=True)

    def get_relations(self, source, destination=None, force=False):
        if destination is None:
            destination = os.path.join(settings.MEDIA_DIR, '.'.join(os.path.basename(source).split('.')[:-1]) + '.json')
        if os.path.isfile(destination) and not force:
            with open(destination, 'r') as f:
                raw_relations = json.load(f)
                return raw_relations
        with open(source, 'r') as f:
            data = yaml.load(f)
        result = []
        self.init_terms()
        self.traverse_structure_and_collect(data, result)
        with open(destination, 'w') as f:
            print(len(result))
            json.dump(result, f)
        return copy.deepcopy(result)

    def traverse_structure_and_collect(self, data, to_save, visited=None):
        if visited is None:
            visited = set()
            for term in data.values():
                self.traverse_structure_and_collect(term, to_save, visited=visited)
            return
        if data['fmaid'] in visited:
            return
        visited.add(data['fmaid'])
        for follow in Command.FOLLOW:
            inserted = set()
            for child in data.get(follow, []):
                child_id = '{}:{}'.format(child.get('taid'), child.get('fmaid'))
                if child_id in inserted:
                    continue
                inserted.add(child_id)
                to_save.append({
                    'type': follow,
                    'term1': self.get_term(data['name'], data.get('taid')),
                    'term2': self.get_term(child['name'], child.get('taid')),
                    'text1': 'FMA{} : {} : {}'.format(data['fmaid'], data.get('taid', 'unknown'), data['name']),
                    'text2': 'FMA{} : {} : {}'.format(child['fmaid'], child.get('taid', 'unknown'), child['name']),
                    'relation_type': 'fma',
                })
            for child in data.get(follow, []):
                self.traverse_structure_and_collect(child, to_save, visited=visited)

    def get_term(self, term_name, term_taid):
        term = self.terms_by_taid.get(term_taid)
        if term is not None:
            return term.to_serializable()
        term = self.terms_by_name.get(term_name)
        return term.to_serializable() if term is not None else None

    def init_terms(self):
        if hasattr(self, 'terms_by_name'):
            return
        terms = Term.objects.prepare_related().all()
        self.terms_by_name = {}
        self.terms_by_taid = {}
        for t in terms:
            for name in t.name_la.split(';'):
                self.terms_by_name[name.lower()] = t
            for name in t.name_en.split(';'):
                self.terms_by_name[name.lower()] = t
            self.terms_by_taid[t.code] = t
