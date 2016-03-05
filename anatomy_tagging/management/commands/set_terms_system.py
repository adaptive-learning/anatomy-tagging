# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from anatomy_tagging.models import Term, Image, Path
from clint.textui import progress


class Command(BaseCommand):
    help = u"""Load terms from csv files"""
    TA_MAPPING = {
        'A01': '01',
        'A02': '02',
        'A03': '03',
        'A04': '04',
        'A05': '05',
        'A06': '06',
        'A07': '06',
        'A08': '07',
        'A09': '08',
        'A12': '09',
        'A13': '10',
        'A14.2': '11',
        'A14.1': '12',
        'A14.0': '12',
        'A15': '13',
        'A16': '13',
        'A11': '14',
        'A10': '15',
    }

    def handle(self, *args, **options):
        terms = Term.objects.all()
        print "Updating terms: "
        for term in progress.bar(terms, every=max(1, len(terms) / 100)):
            code = self.TA_MAPPING.get(
                term.code[:3], self.TA_MAPPING.get(term.code[:5], ""))
            if code != '':
                term.system = code
                term.save()
        topohraphy_images = Image.objects.filter(
            category__name_cs="15 Topografie")
        topohraphy_terms = Term.objects.filter(
            id__in=Path.objects.filter(
                image__in=topohraphy_images).select_related(
                'term').values_list('term', flat=True).distinct())
        print "Updating topohraphy terms: "
        for term in progress.bar(topohraphy_terms, every=max(
                1, len(topohraphy_terms) / 100)):
            if (term is not None and
                    term.slug != 'too-small' and
                    term.slug != 'no-practice' and
                    '15' not in term.system):
                term.system += '15'
                term.save()
