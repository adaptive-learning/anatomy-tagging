# -*- coding: utf-8 -*-
import csv
from os import listdir
from django.core.management.base import BaseCommand
from django.template.defaultfilters import slugify
from anatomy_tagging.models import Term
from anatomy_tagging import settings
from optparse import make_option


class Command(BaseCommand):
    help = u"""Load terms from csv files"""
    option_list = BaseCommand.option_list + (
        make_option(
            '--delete',
            action='store_true',
            dest='delete',
            default=False,
            help='Delete all terms at first',
        ),
    )
    TERMS_DIR = '/terms/'
    slugs = []

    def handle(self, *args, **options):
        if options['delete']:
            Term.objects.all().delete()
        self.slugs = []
        for f in sorted(listdir(settings.MEDIA_DIR + self.TERMS_DIR)):
            if f.endswith('.csv'):
                self.upload_terms(f)

    def upload_terms(self, file_name):
        terms = []
        self.create_special_terms()
        with open(settings.MEDIA_DIR + self.TERMS_DIR + file_name, 'rb') as csvfile:
            terms_reader = csv.reader(csvfile, delimiter='\t')
            next(terms_reader, None)  # skip the headers
            for row in terms_reader:
                if len(row) >= 4 and row[0] != '':
                    slug = slugify(unicode(row[1], 'utf-8'))
                    while slug in self.slugs or Term.objects.exclude(
                            code=row[0]).filter(slug=slug).exists():
                        slug += '_duplicate'
                    self.slugs.append(slug)
                    term = Term(
                        code=row[0],
                        name_la=unicode(row[1], 'utf-8'),
                        name_en=unicode(row[2], 'utf-8'),
                        name_cs=unicode(row[3], 'utf-8'),
                        slug=slug,
                    )
                    if not Term.objects.filter(
                            code=term.code,
                            name_la=term.name_la).exists():
                        terms.append(term)
        print "Uploaded file '" + file_name + "' with %d new terms" % len(terms)
        print "longest slug length: %d" % len(max(self.slugs, key=len))
        # Term.objects.bulk_create(terms)

    def create_special_terms(self):
        try:
            Term.objects.get(slug='no-practice')
        except Term.DoesNotExist:
            term = Term(
                code='no-practice',
                name_la='Vyřazeno z procvičování',
                name_en='Vyřazeno z procvičování',
                name_cs='Vyřazeno z procvičování',
                slug='no-practice',
            )
            term.save()
        try:
            Term.objects.get(slug='too-small')
        except Term.DoesNotExist:
            term = Term(
                code='too-small',
                name_la='too-small',
                name_en='too-small',
                name_cs='too-small',
                slug='too-small',
            )
            term.save()
