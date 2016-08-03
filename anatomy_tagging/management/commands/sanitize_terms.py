# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from anatomy_tagging.models import Term, Path, Relation
import re


class Command(BaseCommand):
    def handle(self, *args, **options):
        subs = {
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
        rev_subs = dict(zip(subs.values(), subs.keys()))
        pattern = re.compile(r'\b(' + '|'.join(rev_subs.keys()).replace('.', '\.') + r')')
        ## print '\b(' + '|'.join(rev_subs.keys()).replace('.', '\.') + r')\b'
        count = 0
        duplicate_count = 0

        terms = Term.objects.all().exclude(code__in=['no-practice', 'too-small'])
        # TODO: this seems too dangerous at the moment
        # self.remove_unused_terms(terms)

        def fix(name):
            name = re.sub('[\(\)]', '', name)
            return '; '.join([n.capitalize() for n in name.split('; ')])

        for t in terms:
            name_la = fix(t.name_la)
            name_la = pattern.sub(lambda x: rev_subs[x.group()], name_la)

            name_cs = fix(t.name_cs)
            name_en = fix(t.name_en)

            if t.name_la != name_la or t.name_cs != name_cs or t.name_en != name_en:
                if t.name_la != name_la:
                    print t.name_la, '->', name_la
                    t.name_la = name_la
                if t.name_cs != name_cs:
                    print t.name_cs, '->', name_cs
                    t.name_cs = name_cs
                if t.name_en != name_en:
                    print t.name_en, '->', name_en
                    t.name_en = name_en
                t.save()
                count += 1
            # TODO merge if on more terms on the same image
            terms = self.find_duplicate_terms(t)
            if len(terms) > 0:
                print t, '->', terms
                print
                duplicate_count += 1
        print count, 'terms updated'
        print duplicate_count, 'duplicate terms found'

    def remove_unused_terms(self, terms):
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
            print 'Removing', t.name_la
            t.delete()
        print len(unused_terms), "unused terms found and deleted"

    def find_duplicate_terms(self, t):
        terms = Term.objects.filter(name_la=t.name_la).exclude(id=t.id)
        ret = []
        for term in terms:
            if self.is_duplicate(term, t):
                # print 'dup', term, t
                ret.append(term)
        return ret

    def is_duplicate(self, t1, t2):
        paths1 = Path.objects.filter(term=t1).select_related('image')
        images1 = [p.image for p in paths1]
        paths2 = Path.objects.filter(term=t2, image__in=images1).select_related('image')
        images2 = [p.image for p in paths2]
        if len(paths2) > 0:
            print list(set(images2))
        return len(paths2) > 0
