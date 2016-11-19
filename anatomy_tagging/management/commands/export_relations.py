# -*- coding: utf-8 -*-
from anatomy_tagging.management.commands.export_flashcards import ExportUtils
from anatomy_tagging.models import Relation, Path, Image
from clint.textui import progress
from collections import defaultdict
from django.core.management.base import BaseCommand
from optparse import make_option
import json


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option(
            '--output',
            dest='output',
            type=str,
            default='relations-flashcards.json'),
        make_option(
            '--relationtype',
            dest='relationtype',
            type=str,
            default=None),
    )

    def handle(self, *args, **options):
        self.options = options
        relations = Relation.objects.prepare_related().filter(type__source='wikipedia')
        relation_type = options.get('relationtype')
        if relation_type is not None and relation_type != '':
            relations = relations.filter(type__identifier=relation_type)
        terms = {}
        categories = ExportUtils.load_categories()
        categories.update({
            'relations': self.RELATIONS_CATEGORY,
            'demo': self.PREMIUM_DEMO_CATEGORY,
        })
        contexts = {}
        flashcards = {}
        for r in progress.bar(relations, every=max(1, len(relations) / 100)):
            if r.term1 is not None and r.term2 is not None:
                terms[r.term1.id] = ExportUtils.term_to_json(r.term1)
                terms[r.term2.id] = ExportUtils.term_to_json(r.term2)
                flashcards[r.id] = self.relation_to_json(r, terms)
                contexts[r.type.identifier] = self.relation_to_context(r)
                categories[r.type.identifier] = self.relation_to_category(r)
                if r.type.identifier == 'Action':
                    # HACK: Use Czech Actions in Czech-Latin terms
                    terms[r.term2.id]['name-cs'] = terms[r.term2.id]['name-cc']
            elif int(options.get('verbosity')) > 0:
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
        id = relation.type.identifier.lower()
        default = {'cs': id, 'en': id}
        c_json = {
            'id': id,
            'name-cs': self.CATEGORIES.get(id, default)['cs'],
            'name-cc': self.CATEGORIES.get(id, default)['cs'],
            'name-en': self.CATEGORIES.get(id, default)['en'],
            'name-la': self.CATEGORIES.get(id, default)['en'],
            'type': 'relation',
            'active': id in self.QUESTIONS,
        }
        return c_json

    def relation_to_context(self, relation):
        id = relation.type.identifier.lower()
        default = {'cs': id, 'en': id}
        c_json = {
            'id': id,
            'content': json.dumps({
                'question': self.QUESTIONS.get(id, self.MISSING_QUESTION),
            }),
            'name-cs': self.CATEGORIES.get(id, default)['cs'],
            'name-cc': self.CATEGORIES.get(id, default)['cs'],
            'name-en': self.CATEGORIES.get(id, default)['en'],
            'name-la': self.CATEGORIES.get(id, default)['en'],
            'active': id in self.QUESTIONS,
        }
        return c_json

    def relation_to_json(self, relation, terms):
        term1_id = ExportUtils.get_term_id(relation.term1)
        term2_id = ExportUtils.get_term_id(relation.term2)
        contexts = self.get_contexts_of_relation(relation)

        r_json = {
            "term": term1_id,
            "term-secondary": term2_id,
            "context": relation.type.identifier.lower(),
            'id': ('%s-%s-%s' % (relation.type.identifier, term1_id[:20], term2_id))[:50],
            "categories": sorted(list(set([relation.type.identifier.lower(), 'relations'] +
                                   terms[relation.term1.id]['categories']))),
            "additional-info": json.dumps(contexts),
        }
        r_json['active'] = r_json['context'] in self.QUESTIONS
        hardcoded_category = self.HARDCODED_CATEGORIES.get('{}:{}'.format(r_json['term'], r_json['context']))
        if hardcoded_category is not None:
            r_json['categories'].append(hardcoded_category)
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
            image = max(images, key=lambda im: self.get_image_size(im, term.system))
            return image.filename_slug[:50]
        elif int(self.options.get('verbosity')) > 0:
            print "WARNING:", 'Term with no image', term

    def get_image_size(self, image, system):
        if not hasattr(self, '_image_sizes'):
            self._image_sizes = {}
            for im in Image.objects.all():
                image_size = defaultdict(set)
                for path in im.path_set.exclude(term=None).select_related('term'):
                    image_size[path.term.system].add(path.term.pk)
                self._image_sizes[im.pk] = {s: len(ts) for s, ts in image_size.items()}
        return self._image_sizes[image.pk].get(system, 0)

    MISSING_QUESTION = {
        'cs': {
            't2ts': u'Chybí text otázky {}',
            'ts2t': u'Chybí text otázky {}',
        },
        'en': {
            't2ts': u'Question text missing {}',
            'ts2t': u'Question text missing {}',
        },
    }
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
            'cs': u'Funkce svalu',
            'en': u'Actions',
        },
        'antagonist': {
            'cs': u'Antagonisté',
            'en': u'Antagonists',
        },
        'insertion': {
            'cs': u'Úpon svalu',
            'en': u'Insertions',
        },
        'origin': {
            'cs': u'Začátek svalu',
            'en': u'Origins',
        },
        'bone': {
            'cs': u'Kosti',
            'en': u'Bones',
        },
        'cranial fossa': {
            'cs': u'Jámy lebeční',
            'en': u'Cranial fossa',
        },
        'vessels': {
            'cs': u'Cévy',
            'en': u'Vessels',
        },
        'nerves': {
            'cs': u'Nervy',
            'en': u'Nerves',
        },
    }
    HARDCODED_CATEGORIES = {
        # {term primary}:{context} -> category
        'A04.6.02.036:insertion': 'demo',
        'A04.6.02.025:insertion': 'demo',
        'A04.6.02.008:nerve': 'demo',
        'A04.3.01.001:artery': 'demo',
        'A04.7.02.007:artery': 'demo',
        'A04.7.02.004:insertion': 'demo',
        'A04.7.02.053:origin': 'demo',
        'A15.2.07.020:antagonist': 'demo',
        'A05.1.04.105:nerve': 'demo',
        'A04.7.02.044:action': 'demo',
        # 'A04.6.02.010:action': 'demo',
        # 'A04.6.02.008:nerve': 'demo',
        # 'A04.7.02.016:action': 'demo',
    }
    PREMIUM_DEMO_CATEGORY = {
        'id': 'demo',
        'name-cs': u'Předplatné: Demo',
        'name-cc': u'Předplatné: Demo',
        'name-en': u'Premium Demo',
        'name-la': u'Premium Demo',
        'active': True,
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
