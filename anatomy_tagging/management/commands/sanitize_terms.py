# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from anatomy_tagging.models import Term, Path
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

        for t in Term.objects.all().exclude(code__in=['no-practice', 'too-small']):
            name_la = t.name_la
            name_la = name_la.capitalize()

            name_la = pattern.sub(lambda x: rev_subs[x.group()], name_la)
            if t.name_la != name_la:
                print t.name_la, '->', name_la
                t.name_la = name_la
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
