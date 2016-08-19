# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from optparse import make_option
from anatomy_tagging.models import Relation, Path
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
        relations = Relation.objects.all().select_related('term1,term2')
        terms = {}
        categories = {}
        categories.update({
            'relations': self.RELATIONS_CATEGORY
        })
        contexts = {}
        flashcards = {}
        for r in progress.bar(relations, every=max(1, len(relations) / 100)):
            if r.term1 is not None and r.term2 is not None:
                terms[r.term1.id] = ExportUtils.term_to_json(r.term1)
                terms[r.term2.id] = ExportUtils.term_to_json(r.term2)
                flashcards[r.id] = self.relation_to_json(r)
                contexts[r.name] = self.relation_to_context(r)
                categories[r.name] = self.relation_to_category(r)
                if r.name == 'Action':
                    # HACK: Use Czech Actions in Czech-Latin terms
                    terms[r.term2.id]['name-cs'] = terms[r.term2.id]['name-cc']
            else:
                print 'WARNING: Missing term in relation %s' % r
        for t in terms.itervalues():
            del t['categories']
            del t['systems']
            if t['name-cc'] == '':
                del t['name-cc']
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
            'type': 'relation',
            'active': True,
        }
        return c_json

    def relation_to_context(self, relation):
        id = relation.name.lower()
        c_json = {
            'id': id,
            'content': json.dumps({
                'question': self.QUESTIONS[id],
            }),
            'name-cs': self.CATEGORIES[id]['cs'],
            'name-cc': self.CATEGORIES[id]['cs'],
            'name-en': self.CATEGORIES[id]['en'],
            'name-la': self.CATEGORIES[id]['en'],
            'active': True,
        }
        return c_json

    def relation_to_json(self, relation):
        term1_id = ExportUtils.get_term_id(relation.term1)
        term2_id = ExportUtils.get_term_id(relation.term2)
        contexts = self.get_contexts_of_relation(relation)

        r_json = {
            "term": term1_id,
            "term-secondary": term2_id,
            "context": relation.name.lower(),
            "active": True,
            "id": "",
            'id': ('%s-%s-%s' % (relation.name, term1_id, term2_id))[:50],
            "categories": [relation.name.lower(), 'relations'],
            "additional-info": json.dumps(contexts),
        }
        return r_json

    def get_contexts_of_relation(self, relation):
        return {
            'contexts': {
                't2ts': self.get_context_of_term(relation.term1),
                'ts2t': self.get_context_of_term(relation.term2),
            },
            'descriptions': {
                't2ts': ExportUtils.term_to_json(relation.term1).get('id'),
                'ts2t': ExportUtils.term_to_json(relation.term2).get('id'),
            },
        }

    def get_context_of_term(self, term):
        paths = Path.objects.filter(term_id=term.id).select_related('image')
        images = list(set([p.image for p in paths if
                           p.image.category is None or
                           '15' not in p.image.category.name_cs]))
        if len(images) > 0:
            return images[0].filename_slug[:50]
        else:
            print "WARNING:", 'Term with no image', term

    QUESTIONS = {
        'nerve': {
            'cs': {
                't2ts': u'Který nerv inervuje sval {}',
                'ts2t': u'Který sval je inervován nervem {}',
            },
            'en': {
                't2ts': u'Which nerve inerves muscle {}',
                'ts2t': u'Which muscle is inerved by {}',
            },
        },
        'artery': {
            'cs': {
                't2ts': u'Která arterie zásobuje sval {}',
                'ts2t': u'Který sval je zásoben arterií {}',
            },
            'en': {
                't2ts': u'Which artery supplies muscle {}',
                'ts2t': u'Which muscle is supplied by {}',
            },
        },
        'action': {
            'cs': {
                't2ts': u'Jaká je funkce svalu {}',
                'ts2t': u'Který sval má funkci {}',
            },
            'en': {
                't2ts': u'What is function of {}',
                'ts2t': u'Which muscle has function {}',
            },
        },
        'antagonist': {
            'cs': {
                't2ts': u'Co je antagonistou svalu {}',
                'ts2t': u'Co je antagonistou svalu {}',
            },
            'en': {
                't2ts': u'What is antagonist of {}',
                'ts2t': u'What is antagonist of {}',
            },
        },
        'insertion': {
            'cs': {
                't2ts': u'Kde má úpon sval {}',
                'ts2t': u'Který sval má úpon na {}',
            },
            'en': {
                't2ts': u'Where is insertion of {}',
                'ts2t': u'Which muscle has insertion on {}',
            },
        },
        'origin': {
            'cs': {
                't2ts': u'Kde má počátek sval {}',
                'ts2t': u'Který sval má počátek na {}',
            },
            'en': {
                't2ts': u'Where is origin of {}',
                'ts2t': u'Which muscle has origin on {}',
            },
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
            'cs': u'Funkce svalů',
            'en': u'Actions',
        },
        'antagonist': {
            'cs': u'Antagonisté',
            'en': u'Antagonists',
        },
        'insertion': {
            'cs': u'Úpony svalů',
            'en': u'Insertions',
        },
        'origin': {
            'cs': u'Začátky svalů',
            'en': u'Origins',
        },
    }
    RELATIONS_CATEGORY = {
        'id': 'relations',
        'name-cs': 'Souvislosti',
        'name-cc': 'Souvislosti',
        'name-en': 'Relations',
        'name-la': 'Relations',
        'active': True,
        'type': 'super',
    }