# -*- coding: utf-8 -*-
from anatomy_tagging.models import Term, Path, Relation, canonical_term_name
from clint.textui import progress
from collections import defaultdict
from django.core.management.base import BaseCommand
from optparse import make_option
from django.db import transaction
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
        )
    )

    def handle(self, *args, **options):
        langs = [options['lang']] if options['lang'] is not None else ['en', 'cs', 'la']
        terms = list(Term.objects.all().exclude(code__in=['no-practice', 'too-small']))
        with transaction.atomic():
            self.make_canonical_names(terms, langs, dry=not options['canonical_names'])
            self.find_duplicate_terms(terms)
            self.remove_unused_terms(terms, dry=not options['remove_unused'])

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
        paths = Path.objects.all().select_related('term')
        relations = Relation.objects.all().select_related('term1,term2')
        used_terms_ids = list(set(
            [p.term_id for p in paths if p.term_id is not None] +
            [r.term1_id for r in relations if r.term1_id is not None] +
            [r.term2_id for r in relations if r.term2_id is not None] +
            [r.term2.parent_id for r in relations if r.term2_id is not None]
        ))
        unused_terms = [t for t in terms if t.id not in used_terms_ids and t.code == '']
        for t in unused_terms:
            if not dry:
                print 'Removing', t.name_la
                t.delete()
            else:
                print '    ', t.name_la
        print len(unused_terms), "unused terms found", ("and deleted" if not dry else "")

    def find_duplicates(self, t):
        terms = Term.objects.filter(name_la=t.name_la).exclude(id=t.id)
        ret = []
        for term in terms:
            if self.is_duplicate(term, t):
                ret.append(term)
        return ret

    def is_duplicate(self, t1, t2):
        paths1 = Path.objects.filter(term=t1).select_related('image')
        images1 = [p.image for p in paths1]
        paths2 = Path.objects.filter(term=t2, image__in=images1).select_related('image')
        images2 = [p.image for p in paths2]
        # if len(paths2) > 0:
            # print list(set(images2))
        return len(paths2) > 0
