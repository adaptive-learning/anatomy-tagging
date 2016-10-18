# -*- coding: utf-8 -*-
from anatomy_tagging.models import Term
from clint.textui import progress
from django.core.management.base import BaseCommand
from django.db import transaction
from optparse import make_option
import re


class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option(
            '--lang',
            dest='lang',
            type=str,
            default=None),
    )

    def handle(self, *args, **options):
        if options['lang'] is not None:
            langs = [options['lang']]
        else:
            langs = ['en', 'cs', 'en']
        with transaction.atomic():
            for term in progress.bar(Term.objects.all(), every=max(1, Term.objects.all().count() / 100)):
                changed = False
                for lang in langs:
                    name = getattr(term, 'name_{}'.format(lang))
                    parts = '; '.join(p.strip() for p in name.split(';')).split(' ')
                    canonical_name = ' '.join([Command.make_canonical(p.strip()) for p in parts]).replace(' A ', ' a ').replace(' S ', ' s ')
                    canonical_name = re.sub(r'(\S)([-])(\S)', r'\1 \2 \3', canonical_name, re.UNICODE)
                    canonical_name = re.sub(r',(\S)', r', \1', canonical_name, re.UNICODE)
                    if name != canonical_name:
                        changed = True
                        setattr(term, 'name_{}'.format(lang), canonical_name)
                if changed:
                    term.save()

    @staticmethod
    def make_canonical(value):
        if Command.is_roman_number(value) or Command.is_location(value):
            return value.upper()
        if Command.is_name(value):
            return '\''.join(p.title() if i == 0 else p for i, p in enumerate(value.split('\'')))
        filtered = ''.join(re.findall("\w+", value, flags=re.UNICODE))
        if filtered.lower() in ['vb', 'va']:
            return value.lower().replace('v', 'V')
        return value.lower()

    @staticmethod
    def is_roman_number(value):
        value = value.lower()
        letters = {l for l in ''.join(re.findall("[^\W\d_]+", value, flags=re.UNICODE))}
        if letters <= {u'i', u'v', u'x'}:
            return True
        else:
            return False

    @staticmethod
    def is_location(value):
        filtered = ''.join(re.findall("\w+", value, flags=re.UNICODE))
        if len(filtered) == 1:
            return True
        return bool(re.search(r'\d', value))

    @staticmethod
    def is_name(value):
        value_lower = value.lower().strip(';')
        if any([value_lower.endswith(ext) for ext in ['ovo', u'ův', 'ova', 'ovi', 'ovy']]) or value_lower.endswith('\'s'):
            return True
        if value_lower in ['sorgius']:
            return True
        return False
