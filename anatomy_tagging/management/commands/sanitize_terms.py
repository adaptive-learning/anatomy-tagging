# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from anatomy_tagging.models import Term
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
        count = 0

        for t in Term.objects.all().exclude(code__in=['no-practice', 'too-small']):
            name_la = t.name_la
            name_la = name_la.capitalize()

            name_la = pattern.sub(lambda x: rev_subs[x.group()], name_la)
            if t.name_la != name_la:
                print t.name_la, '->', name_la
                t.name_la = name_la
                t.save()
                count += 1
        print count, 'terms updated'
