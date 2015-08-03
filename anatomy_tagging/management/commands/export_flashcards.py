# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from optparse import make_option
from anatomy_tagging.models import Category, Term, Image
import hashlib
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
                        p_json['term'] = hashlib.sha1(p.term.slug).hexdigest()
                    used_terms.add(p_json['term'])
                    if i.category is not None:
                        term_json = terms[p_json['term']]
                        term_categories = term_json.get('categories', [])
                        term_categories.append(self._get_category_id(i.category))
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
            }
            result[c_json['id']] = c_json
        return result, used_terms

    def load_terms(self):
        result = {}
        for t in Term.objects.all().exclude(code__in=['no-practice', 'too-small']):
            t_json = {
                'id': t.code if t.code else hashlib.sha1(t.slug).hexdigest(),
                'name-cs': self._empty(t.name_la),
                'name-en': self._empty(t.name_en),
            }
            if t.body_part is not None:
                t_json['categories'] = self._body_part_to_categories(t.body_part)
            result[t_json['id']] = t_json
        return result

    def load_categories(self):
        result = {}
        for c in Category.objects.all():
            c_json = {
                'id': self._get_category_id(c),
                'name-cs': self._empty(c.name_cs),
                'name-en': self._get_category_english_name(c),
                'type': 'system',
            }
            if c.parent is not None:
                c_json['parent-categories'] = [self._get_category_id(c.parent)]
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

    def _get_category_id(self, c):
        try:
            return str(int(c.name_cs.split()[0])).zfill(2)
        except (ValueError, IndexError):
            return str(c.id)

    def _get_category_english_name(self, c):
        if c.name_en is not None and c.name_en != '':
            return c.name_en
        try:
            id = int(c.name_cs.split()[0])
            return str(id) + ' ' + self.ENGLISH_CATEGORY_NAMES[id]
        except (ValueError, IndexError):
            return self._empty(c.name_en)

    LOCATION_CATEGORIES = [
        {
            'id': 'Hf',
            'name-cs': 'Hlava, obličejová část (splanchnokranium)',
            'name-en': 'Head - Face',
        },
        {
            'id': 'Hb',
            'name-cs': 'Hlava, mozková část (neurokranium)',
            'name-en': 'Head - Brain',
        },
        {
            'id': 'N',
            'name-cs': 'Krk',
            'name-en': 'Neck',
        },
        {
            'id': 'T',
            'name-cs': 'Hrudník',
            'name-en': 'Thorax',
        },
        {
            'id': 'B',
            'name-cs': 'Záda',
            'name-en': 'Back',
        },
        {
            'id': 'A',
            'name-cs': 'Břicho',
            'name-en': 'Abdomen',
        },
        {
            'id': 'P',
            'name-cs': 'Pánev',
            'name-en': 'Pelvis',
        },
        {
            'id': 'UE',
            'name-cs': 'Horní končetina',
            'name-en': 'Upper Extremity',
        },
        {
            'id': 'LE',
            'name-cs': 'Dolní končetina',
            'name-en': 'Lower Extremity',
        },
    ]

    ENGLISH_CATEGORY_NAMES = {
        1: 'General anatomy',
        2: 'Bones',
        3: 'Joints',
        4: 'Muscles',
        5: 'Digestive system',
        6: 'Respiratory system',
        7: 'Urinary system',
        8: 'Genital system',
        9: 'Heart and blood vessels',
        10: 'Lymphatic and immune system',
        11: 'Peripheral nervous system',
        12: 'Central nervous system',
        13: 'Sense and skin',
        14: 'Endocrine system',
        15: 'Topography',
    }
