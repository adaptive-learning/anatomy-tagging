# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from optparse import make_option
from anatomy_tagging.models import Category, Term, Image
import json


class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option(
            '--output',
            dest='output',
            type=str,
            default='anatomy-flashcards.json'),
        )

    def handle(self, *args, **options):
        categories = self.load_categories()
        terms = self.load_terms()
        contexts, used_terms = self.load_contexts(terms)
        terms = dict(filter(lambda (i, t): i in used_terms, terms.items()))
        flashcards = self.load_flashcards(contexts)
        for c in contexts.itervalues():
            c['content'] = json.dumps(c['content'])
        with open(options['output'], 'w') as f:
            json.dump({
                'categories': categories.values(),
                'terms': terms.values(),
                'contexts': contexts.values(),
                'flashcards': flashcards.values()
            }, f, indent=2)

    def load_flashcards(self, contexts):
        result = {}
        for c in contexts.itervalues():
            for p in c['content']['paths']:
                if 'term' not in p:
                    continue
                f_json = {
                    'id': ('%s-%s' % (p['term'], c['id']))[:50],
                    'term': p['term'],
                    'context': c['id'],
                    'description': p['term'],
                }
                result[f_json['id']] = f_json
        return result

    def load_contexts(self, terms):
        result = {}
        used_terms = set()
        for i in Image.objects.select_related('bbox').prefetch_related('path_set').all():
            paths = []
            for p in i.path_set.all():
                p_json = {
                    'd': p.d,
                    'color': p.color,
                    'opacity': p.opacity,
                }
                if p.bbox is not None:
                    p_json['bbox'] = self._bbox_to_json(p.bbox)
                if p.term is not None and p.term.code not in ['no-practice', 'too-small']:
                    if p.term.code:
                        p_json['term'] = p.term.code
                    else:
                        p_json['term'] = p.term.slug
                    used_terms.add(p_json['term'])
                    if i.category is not None:
                        term_json = terms[p_json['term']]
                        term_categories = term_json.get('categories', [])
                        term_categories.append(str(i.category.id))
                        term_json['categories'] = list(set(term_categories))
                if p.stroke is not None:
                    p_json['stroke'] = p.stroke
                    p_json['stroke_width'] = p.stroke_width
                paths.append(p_json)
            content = {
                'meta': {
                    'textbook-page': i.textbook_page,
                    'filename': i.filename,
                },
                'bbox': self._bbox_to_json(i.bbox),
                'paths': paths
            }
            c_json = {
                'id': i.filename_slug[:50],
                'content': content,
                'name-cs': self._empty(i.name_cs),
                'name-en': self._empty(i.name_en),
                'name-la': '',  # TODO
            }
            result[c_json['id']] = c_json
        return result, used_terms

    def load_terms(self):
        result = {}
        for t in Term.objects.all().exclude(code__in=['no-practice', 'too-small']):
            t_json = {
                'id': t.code if t.code else t.slug,
                'name-cs': self._empty(t.name_cs),
                'name-en': self._empty(t.name_en),
                'name-la': self._empty(t.name_la),
            }
            if t.body_part is not None:
                t_json['categories'] = self._body_part_to_categories(t.body_part)
            result[t_json['id']] = t_json
            if t_json['id'] == 'trigonum-omotrapezium':
                print t_json
        return result

    def load_categories(self):
        result = {}
        for c in Category.objects.all():
            c_json = {
                'id': str(c.id),
                'name-cs': self._empty(c.name_cs),
                'name-en': self._empty(c.name_en),
                'name-la': '',  # TODO
            }
            if c.parent is not None:
                c_json['parent-categories'] = [str(c.parent)]
            result[c_json['id']] = c_json
        for c in self.LOCATION_CATEGORIES:
            c['type'] = 'location'
            c['not-in-model'] = True
            result[c['id']] = c
        return result

    def _bbox_to_json(self, bbox):
        return {
            'x': bbox.x,
            'y': bbox.y,
            'width': bbox.width,
            'height': bbox.height,
        }

    def _body_part_to_categories(self, body_part):
        result = []
        for c in ['Hf', 'Hb', 'UE', 'LE']:
            if c in body_part:
                result.append(c)
                body_part = body_part.replace(c, '')
        for c in body_part:
            if c == 'H':
                result.extend(['Hf', 'Hb'])
            else:
                result.append(c)
        return result

    def _empty(self, x):
        return '' if x is None else x

    LOCATION_CATEGORIES = [
        {
            'id': 'Hf',
            'name-cs': '',
            'name-en': '',
            'name-la': '',
        },
        {
            'id': 'Hb',
            'name-cs': '',
            'name-en': '',
            'name-la': '',
        },
        {
            'id': 'N',
            'name-cs': '',
            'name-en': '',
            'name-la': '',
        },
        {
            'id': 'T',
            'name-cs': '',
            'name-en': '',
            'name-la': '',
        },
        {
            'id': 'B',
            'name-cs': '',
            'name-en': '',
            'name-la': '',
        },
        {
            'id': 'A',
            'name-cs': '',
            'name-en': '',
            'name-la': '',
        },
        {
            'id': 'P',
            'name-cs': '',
            'name-en': '',
            'name-la': '',
        },
        {
            'id': 'UE',
            'name-cs': '',
            'name-en': '',
            'name-la': '',
        },
        {
            'id': 'LE',
            'name-cs': '',
            'name-en': '',
            'name-la': '',
        },
    ]
