# -*- coding: utf-8 -*-
from anatomy_tagging.management.commands.export_flashcards import ExportUtils
from anatomy_tagging.models import Relation, Path, Image, Term
from clint.textui import progress
from collections import defaultdict
from django.core.management.base import BaseCommand
from optparse import make_option
import json
from django.template.defaultfilters import slugify


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
        relations = Relation.objects.prepare_related().filter(type__ready=True, state=Relation.STATE_VALID[0])
        print(relations.query)
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
                flashcards[r.id] = self.relation_to_flashcard(r, contexts, categories, terms)
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

    def relation_to_context(self, relation, all_contexts):
        id = my_slugify(relation.type.identifier)
        if id in all_contexts:
            return id
        c_json = {
            'id': id,
            'content': json.dumps({
                'question': {
                    'cs': json.loads(relation.type.question_cs),
                    'en': json.loads(relation.type.question_en),
                },
            }),
            'name-cs': relation.type.name_cs,
            'name-cc': relation.type.name_cs,
            'name-en': relation.type.name_en,
            'name-la': relation.type.name_en,
            'active': relation.type.ready,
        }
        all_contexts[id] = c_json
        return id

    def relation_to_categories(self, relation, all_categories, terms):
        id = my_slugify(relation.type.identifier)
        result = [id]
        category = self.CATEGORIES.get(id, {})
        # relation type category
        if id not in all_categories:
            c_json = {
                'id': id,
                'name-cs': relation.type.name_cs,
                'name-cc': relation.type.name_cs,
                'name-en': relation.type.name_en,
                'name-la': relation.type.name_en,
                'display-priority': relation.type.display_priority,
                'type': category.get('type', 'relation'),
                'active': relation.type.ready,
            }
            all_categories[id] = c_json
        # term categories
        result.extend(terms[relation.term1.id]['categories'])
        if 'parent' in category:
            parent_id = category['parent']
            if parent_id not in all_categories:
                parent = self.CATEGORIES[parent_id]
                all_categories[parent_id] = {
                    'id': parent_id,
                    'name-cs': parent['cs'],
                    'name-cc': parent['cs'],
                    'name-en': parent['en'],
                    'name-la': parent['en'],
                    'display-priority': parent.get('display-priority', 0),
                    'active': parent.get('active', True),
                }
            result.append(parent_id)
        return result

    def relation_to_flashcard(self, relation, all_contexts, all_categories, all_terms):
        if relation.term1.id not in all_terms:
            all_terms[relation.term1.id] = ExportUtils.term_to_json(relation.term1)
        if relation.term2.id not in all_terms:
            all_terms[relation.term2.id] = ExportUtils.term_to_json(relation.term2)
        term1_id = ExportUtils.get_term_id(relation.term1)
        term2_id = ExportUtils.get_term_id(relation.term2)
        contexts = self.get_contexts_of_relation(relation)

        r_json = {
            "term": term1_id,
            "term-secondary": term2_id,
            "context": self.relation_to_context(relation, all_contexts),
            'id': ('%s-%s-%s' % (relation.type.identifier, term1_id[:20], term2_id))[:50],
            "categories": self.relation_to_categories(relation, all_categories, all_terms),
            "additional-info": json.dumps(contexts),
        }
        r_json['restrict-open-questions'] = not Term.objects.is_code_terminologia_anatomica(r_json['term-secondary'])
        r_json['disable-open-questions'] = not Term.objects.is_code_terminologia_anatomica(r_json['term'])
        r_json['active'] = all_contexts[r_json['context']]['active']
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

    CATEGORIES = {
        'foramina': {
            'cs': u'Foramina',
            'en': u'Foramina',
            'display-priority': 70,
        },
        'bone': {
            'parent': 'foramina',
            'type': 'subrelation',
        },
        'cranialfossa': {
            'parent': 'foramina',
            'type': 'subrelation',
        },
        'vessels': {
            'parent': 'foramina',
            'type': 'subrelation',
        },
        'nerves': {
            'parent': 'foramina',
            'type': 'subrelation',
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


def my_slugify(string):
    return slugify(string).replace('-', '')
