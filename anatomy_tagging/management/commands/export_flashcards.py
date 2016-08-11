# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
from optparse import make_option
from anatomy_tagging.models import Category, Term, Image
import hashlib
import json
from clint.textui import progress


class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option(
            '--output',
            dest='output',
            type=str,
            default='anatomy-flashcards.json'),
        make_option(
            '--context',
            help='export only a single context specified by filename_slug',
            dest='context',
            type=str,
            default=None),
        make_option(
            '--skip_check',
            help='do not check that there is no issues in the data',
            dest='skip_check',
            action="store_true",
            default=False),
    )

    def handle(self, *args, **options):
        categories = ExportUtils.load_categories()
        terms = self.load_terms()
        contexts, used_terms, used_categories = self.load_contexts(
            terms, options['context'])
        terms = dict(filter(lambda (i, t): i in used_terms, terms.items()))
        flashcards = self.load_flashcards(contexts, terms)
        if options['context'] is not None:
            options['output'] = options['output'].replace(
                '.json', '-' + options['context'] + '.json')
            categories = dict(filter(lambda (i, c): i in used_categories, categories.items()))
        for c in contexts.itervalues():
            c['content'] = json.dumps(c['content'])
        output_dict = {
            'categories': categories.values(),
            'terms': terms.values(),
            'contexts': contexts.values(),
            'flashcards': flashcards.values()
        }
        if not options['skip_check']:
            self.check_validity(terms, flashcards)
        with open(options['output'], 'w') as f:
            json.dump(output_dict, f, indent=2)
            print 'Flashcards exported to file: \'%s\'' % options['output']

    def check_validity(self, terms, flashcards):
        for term in terms.values():
            if term['name-en'] == '':
                raise CommandError(
                    u'Pojmu "%s" chybí anglický překlad' % term['name-cs'])
        self.check_duplicity(terms, 'name-cs')
        self.check_duplicity(terms, 'name-en')

    def check_duplicity(self, terms, key):
        terms_by_name_cs = {}
        for term in terms.values():
            if term[key] in terms_by_name_cs:
                raise CommandError(
                    u'Duplicitní pojem s názvem "%s"' % term[key])
            terms_by_name_cs[term[key]] = term

    def load_flashcards(self, contexts, terms):
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
                    'active': c['active'],
                    'categories': list(terms[p['term']]['categories'])
                }
                if c['category'] == '15':
                    f_json['categories'].append(c['category'])
                if len(terms[p['term']]['systems']) == 0 and c['category'] is not None:
                    f_json['categories'].append(c['category'])
                f_json['categories'] = list(set(f_json['categories'] + ['images']))
                result[f_json['id']] = f_json
        for t in terms.itervalues():
            del t['categories']
            del t['systems']
            if t['name-cc'] == '':
                del t['name-cc']
        for c in contexts.itervalues():
            del c['category']
        return result

    def load_contexts(self, terms, context):
        result = {}
        used_terms = set()
        used_categories = set()
        print "\nLoading contexts"
        images = Image.objects.select_related('bbox').prefetch_related('path_set').all()
        if context is not None:
            images = images.filter(filename_slug=context)
        for i in progress.bar(images, every=max(1, len(images) / 100)):
            terms_in_image = set()
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
                    terms_in_image.add(p_json['term'])
                    if i.category is not None:
                        term_json = terms[p_json['term']]
                        term_categories = term_json.get('categories', [])
                        term_json['categories'] = list(set(term_categories))
                        used_categories |= set(term_json['categories'])
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
                'name-cs': ExportUtils._empty(i.name_cs),
                'name-cc': ExportUtils._empty(i.name_cs),
                'name-en': ExportUtils._empty(i.name_en),
                'name-la': ExportUtils._empty(i.name_en),
                'active': i.active and len(terms_in_image) > 1,
                'category': ExportUtils._get_category_id(i.category) if i.category is not None else None,
            }
            if len(terms_in_image) <= 1:
                print "WARNING: Deactivating image with %s terms:" % len(terms_in_image), i.filename.encode('utf8')
            result[c_json['id']] = c_json
        return result, used_terms, used_categories

    def load_terms(self):
        result = {}
        for t in Term.objects.all().exclude(code__in=['no-practice', 'too-small']):
            t_json = ExportUtils.term_to_json(t)
            result[t_json['id']] = t_json
        return result

    def _bbox_to_json(self, bbox):
        if bbox is None:
            return None
        return {
            'x': bbox.x,
            'y': bbox.y,
            'width': bbox.width,
            'height': bbox.height,
        }


class ExportUtils(object):
    @staticmethod
    def _stip_number(x):
        return filter(lambda c: not c.isdigit(), x).strip()

    @staticmethod
    def _get_category_id(c):
        try:
            return str(int(c.name_cs.split()[0])).zfill(2)
        except (ValueError, IndexError):
            return str(c.id)

    @staticmethod
    def _get_category_english_name(c):
        if c.name_en is not None and c.name_en != '':
            return c.name_en
        try:
            id = int(c.name_cs.split()[0])
            return ExportUtils.ENGLISH_CATEGORY_NAMES[id]
        except (ValueError, IndexError):
            return ExportUtils._empty(c.name_en)

    LOCATION_CATEGORIES = [
        {
            'id': 'Hf',
            'name-cs': 'Splanchnokranium',
            'name-en': 'Head - Face',
        },
        {
            'id': 'Hb',
            'name-cs': 'Neurokranium',
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

    @staticmethod
    def load_categories():
        result = {}
        for c in Category.objects.exclude(name_cs=''):
            c_json = {
                'id': ExportUtils._get_category_id(c),
                'name-cs': ExportUtils._stip_number(ExportUtils._empty(c.name_cs)),
                'name-cc': ExportUtils._stip_number(ExportUtils._empty(c.name_cs)),
                'name-en': ExportUtils._get_category_english_name(c),
                'name-la': ExportUtils._get_category_english_name(c),
                'type': 'system',
            }
            if c.parent is not None:
                c_json['parent-categories'] = [ExportUtils._get_category_id(c.parent)]
            result[c_json['id']] = c_json
        for c in ExportUtils.LOCATION_CATEGORIES:
            c['type'] = 'location'
            c['name-la'] = c['name-en']
            c['name-cc'] = c['name-cs']
            c['not-in-model'] = True
            result[c['id']] = c
        result['images'] = {
            'id': 'images',
            'name-cs': 'Pojmy na obrázku',
            'name-cc': 'Pojmy na obrázku',
            'name-en': 'Terms in images',
            'name-la': 'Terms in images',
            'type': 'super',
        }
        return result

    @staticmethod
    def _empty(x, y=None):
        ret = '' if x is None else x
        if ret == '' and y is not None:
            ret = y
        return ret

    @staticmethod
    def _body_part_to_categories(body_part):
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

    @staticmethod
    def _system_to_categories(systems):
        system_ids = [str(i).zfill(2) for i in range(1, 14)]
        result = []
        for i in range(0, len(systems), 2):
            system_id = systems[i: i + 2]
            if system_id in system_ids:
                result.append(system_id)
        return result

    @staticmethod
    def term_to_json(t):
        t_json = {
            'id': t.code if t.code else hashlib.sha1(t.slug).hexdigest(),
            'name-cs': ExportUtils._empty(t.name_la, t.name_cs),
            'name-cc': ExportUtils._empty(t.name_cs, t.name_la),
            'name-en': ExportUtils._empty(t.name_en, t.name_la),
            'name-la': ExportUtils._empty(t.name_la, t.name_en),
        }
        # Translations hack: name_la is likely in English, so use name_cs
        #  for Czech Latin instead
        if 'of the' in t.name_la:
            t_json['name-cs'] = t.name_cs
        if t.body_part is not None:
            t_json['categories'] = ExportUtils._body_part_to_categories(t.body_part)
        if t.system is not None:
            t_json['systems'] = ExportUtils._system_to_categories(t.system)
            t_json['categories'] = t_json['systems'] + (
                t_json.get('categories', []))
        return t_json

    @staticmethod
    def get_term_id(t):
        return t.code if t.code else hashlib.sha1(t.slug).hexdigest()
