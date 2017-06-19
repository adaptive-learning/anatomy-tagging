# -*- coding: utf-8 -*-
from anatomy_tagging import settings
from anatomy_tagging.models import Term, Path, canonical_term_name
from clint.textui import progress
from collections import defaultdict
from django.core.management.base import BaseCommand
from django.db import transaction
from optparse import make_option
import json
import re


class Command(BaseCommand):

    SUBS = {
        'Musculi': 'Mm.',
        'Venae': 'Vv.',
        'Nervi': 'Nn.',
        'Arteriae': 'Aa.',
        'Rami': 'Rr.',
        'Ligamenta': 'Ligg.',
        'Musculus': 'M.',
        'Vena': 'V.',
        'Nervus': 'N.',
        'Arteria': 'A.',
        'Ramus': 'R.',
        'Ligamentum': 'Lig.',
    }

    option_list = BaseCommand.option_list + (
        make_option(
            '--lang',
            dest='lang',
            type=str,
            default=None),
        make_option(
            '--canonical-names',
            dest='canonical_names',
            action='store_true',
            default=False
        ),
        make_option(
            '--remove-unused',
            dest='remove_unused',
            action='store_true',
            default=False
        ),
        make_option(
            '--find-duplicates',
            dest='find_duplicates',
            action='store_true',
            default=False
        ),
        make_option(
            '--fix-duplicate-codes',
            dest='fix_duplicate_codes',
            action='store_true',
            default=False
        ),
        make_option(
            '--fill-fma',
            dest='fill_fma',
            action='store_true',
            default=False
        ),
    )

    def handle(self, *args, **options):
        langs = [options['lang']] if options['lang'] is not None else ['en', 'cs', 'la']
        terms = list(Term.objects.all().exclude(code__in=['no-practice', 'too-small']))
        with transaction.atomic():
            self.fix_duplicate_codes(terms, dry=not options['fix_duplicate_codes'])
            self.make_canonical_names(terms, langs, dry=not options['canonical_names'])
            if options['find_duplicates']:
                self.find_duplicate_terms(terms)
            self.remove_unused_terms(terms, dry=not options['remove_unused'])
            if options['fill_fma']:
                self.fill_fma()

    def fix_duplicate_codes(self, terms, lang='la', used_only=False, dry=True):
        print 'Fixing duplicate term codes'
        used_ids = {t.id for t in Term.objects.all_used()}
        if used_only:
            terms = [t for t in terms if t.id in used_ids]
        groupped = defaultdict(list)
        for t in terms:
            if t.code == '':
                continue
            groupped[t.code].append(t)
        filtered = {code: ts for code, ts in groupped.items() if len(ts) > 1}
        images_to_export = set()
        for code, ts in filtered.items():
            print code
            terms_updated = False
            for t in ts:
                print '  ',
                print t.id, '\t', t.fma_id, t.name_la, '|', t.name_en, '|', t.name_cs
                term_updated = False
                if u'♀' in getattr(t, 'name_{}'.format(lang)) and 'F' not in t.code:
                    print('      CONVERTING CODE TO FEMALE VERSION')
                    term_updated = True
                    if not dry:
                        t.code = '{}F'.format(t.code)
                        t.save()
                if u'♂' in getattr(t, 'name_{}'.format(lang)) and 'M' not in t.code:
                    print('      CONVERTING CODE TO MALE VERSION')
                    term_updated = True
                    if not dry:
                        t.code = '{}M'.format(t.code)
                        t.save()
                for p in t.path_set.filter(image__active=True).select_related('image'):
                    print '      image', p.image.filename
                    if term_updated:
                        images_to_export.add(p.image.filename)
                if term_updated:
                    terms_updated = True
            if not terms_updated and len({t.fma_id for t in ts if t.fma_id != -1}) <= 1:
                to_survive = min(ts, key=lambda t: t.id)
                print '  ', 'MERGING ALL AS', to_survive.id
                for to_merge in [t for t in ts if t.id != to_survive.id]:
                    if not dry:
                        Term.objects.merge_terms(to_survive, to_merge)
                    for p in t.path_set.filter(image__active=True).select_related('image'):
                        images_to_export.add(p.image.filename)
            elif not terms_updated:
                print '  ', 'NOT RESOLVED'
        print 'IMAGES TO EXPORT:'
        for i in sorted(images_to_export):
            print '  ', i

    def find_duplicate_terms(self, terms, lang='la'):
        print 'Looking for duplicates'
        duplicates = {}
        for term in progress.bar(terms):
            ds = self.find_duplicates(term)
            if len(ds) > 0:
                duplicates[term] = ds
        for term, ds in duplicates.items():
            print term
            for d in ds:
                print '    -', d
        print 'Found duplicates:', len(duplicates)
        return len(duplicates)

    def make_canonical_names(self, terms, langs, dry):
        print 'Canonical term names'
        rev_subs = {v.lower(): k.lower() for k, v in self.SUBS.items()}
        pattern = re.compile(r'\b(' + '|'.join(rev_subs.keys()).replace('.', '\.') + r')')
        count = 0
        for term in terms:
            changed = False
            for lang in langs:
                name = getattr(term, 'name_{}'.format(lang))
                canonical_name = pattern.sub(lambda x: rev_subs[x.group()], name) if lang == 'la' else name
                canonical_name = canonical_term_name(name)
                if name != canonical_name:
                    print name.encode('utf-8'), '->', canonical_name.encode('utf-8')
                    changed = True
                    setattr(term, 'name_{}'.format(lang), canonical_name)
            if changed:
                count += 1
                if not dry:
                    term.save()
        print 'Terms to be updated:' if dry else 'Updated terms:', count

    def remove_unused_terms(self, terms, dry):
        print 'Looking for unused terms'
        used_ids = {t.id for t in Term.objects.all_used()}
        to_remove = [t for t in terms if t.id not in used_ids and t.code == '']
        for t in to_remove:
            if not dry:
                print 'Removing', t.name_la.encode('utf-8')
                t.delete()
            else:
                print '    ', t.name_la.encode('utf-8')
        print len(to_remove), "unused terms found", ("and deleted" if not dry else "")

    def find_duplicates(self, t):
        terms = Term.objects.filter(name_la=t.name_la).exclude(id=t.id)
        ret = []
        for term in terms:
            if self.is_duplicate(term, t):
                ret.append(term)
        return ret

    def fill_fma(self):
        print 'Filling FMA IDs'
        with open('{}/fma_ta_mapping.json'.format(settings.MEDIA_DIR), 'r') as f:
            mapping = json.load(f)
        ta2fma = defaultdict(list)
        for fma, ta in mapping.items():
            ta2fma[ta].append(int(fma.replace('FMA', '')))
        for term in progress.bar(Term.objects.filter(fma_id=-1)):
            found_fmas = ta2fma[term.code]
            if len(found_fmas) == 1:
                term.fma_id = found_fmas[0]
                term.save()

    def is_duplicate(self, t1, t2):
        paths1 = Path.objects.filter(term=t1).select_related('image')
        images1 = [p.image for p in paths1]
        paths2 = Path.objects.filter(term=t2, image__in=images1).select_related('image')
        images2 = [p.image for p in paths2]
        # if len(paths2) > 0:
            # print list(set(images2))
        return len(paths2) > 0
