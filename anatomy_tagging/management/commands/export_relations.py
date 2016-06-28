# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
from optparse import make_option
from anatomy_tagging.models import Category, Term, Image, Relation
import hashlib
import json
from clint.textui import progress
from anatomy_tagging.management.commands.export_flashcards import ExportUtils


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option(
            '--output',
            dest='output',
            type=str,
            default='relations-flashcards.json'),
    )

    def handle(self, *args, **options):
        relations = Relation.objects.all()
        terms = {}
        categories = {}
        contexts = {}
        flashcards = {}
        for r in relations:
            if r.term1 is not None and r.term2 is not None:
                terms[r.term1.id] = ExportUtils.term_to_json(r.term1)
                terms[r.term2.id] = ExportUtils.term_to_json(r.term2)
                flashcards[r.id] = self.relation_to_json(r)
                contexts[r.name] = self.relation_to_context(r)
                categories[r.name] = self.relation_to_category(r)
                print r
        print 'hey'
        output_dict = {
            'categories': categories.values(),
            'terms': terms.values(),
            'contexts': contexts.values(),
            'flashcards': flashcards.values()
        }
        with open(options['output'], 'w') as f:
            json.dump(output_dict, f, indent=2)
            print 'Flashcards exported to file: \'%s\'' % options['output']

    def relation_to_category(self, relation):
        id = relation.name.lower()
        c_json = {
            'id': id,
            'name-cs': self.CATEGORIES[id]['cs'],
            'name-cc': self.CATEGORIES[id]['cs'],
            'name-en': self.CATEGORIES[id]['en'],
            'name-la': self.CATEGORIES[id]['en'],
            'active': True,
        }
        return c_json

    def relation_to_context(self, relation):
        id = relation.name.lower()
        c_json = {
            'id': id,
            'content': {
                'question': self.QUESTIONS[id],
            },
            'name-cs': '',
            'name-cc': '',
            'name-en': '',
            'name-la': '',
            'active': True,
        }
        return c_json

    def relation_to_json(self, relation):
        term1_id = ExportUtils.get_term_id(relation.term1)
        term2_id = ExportUtils.get_term_id(relation.term2)

        r_json = {
            "term1": term1_id,
            "term2": term2_id,
            "context": relation.name.lower(),
            "active": True,
            "id": "",
            'id': ('%s-%s-%s' % (relation.name, term1_id, term2_id))[:50],
            "categories": [relation.name.lower()],
        }
        return r_json
    QUESTIONS = {
        'nerve': {
            'cs': u'Který nerv inervuje sval {}?',
        },
        'artery': {
            'cs': u'Která arterie zásobuje sval {}?',
        },
        'action': {
            'cs': u'Jaká je funkce svalu {}?',
        },
        'antagonist': {
            'cs': u'Co je antagonistou svalu {}?',
        },
        'insertion': {
            'cs': u'Kde má úpon sval {}?',
        },
        'origin': {
            'cs': u'Kde má počátek sval {}?',
        },
    }
    CATEGORIES = {
        'nerve': {
            'cs': u'Inervace',
            'en': u'Nerve supply',
        },
        'artery': {
            'cs': u'Cévní zásobení',
            'en': u'Arterial supply',
        },
        'action': {
            'cs': u'Funkce',
            'en': u'Actions',
        },
        'antagonist': {
            'cs': u'Antagonisté',
            'en': u'Antagonists',
        },
        'insertion': {
            'cs': u'Úpony',
            'en': u'Insertions',
        },
        'origin': {
            'cs': u'Počátky',
            'en': u'Origins',
        },
    }
