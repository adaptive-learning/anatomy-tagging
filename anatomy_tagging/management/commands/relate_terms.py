# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from anatomy_tagging.models import Term
import re


class Command(BaseCommand):
    help = u"""Relate terms based on codes"""

    def handle(self, *args, **options):
        terms = Term.objects.all()
        exists = 0
        not_exists = 0
        for t in terms:
            if t.code != '':
                parent = find_parent(t)
                if parent is not None:
                    exists += 1
                else:
                    not_exists += 1
                if parent is not None and t.parent is None:
                    t.parent = parent
                    t.save()
        print 'Related:', exists, 'not related:', not_exists


def fix_multiple(code):
    terms = Term.objects.filter(code=code)
    first = terms[0]
    for t in terms:
        if first.name_la == t.name_la and first.id != t.id:
            print "deteting", t
            t.delete()


def find_parent(t, debug=False):
    replaces = [
        (r'\.\d{3}', '.001'),
        (r'\.\d{3}', '.000'),
        (r'\d{2}\.001$', '00.001'),
        (r'\d{2}\.001$', '01.001'),
        (r'\d\.01\.001$', '0.00.000'),
        (r'\d\.00\.001$', '0.00.000'),
    ]
    parent = None
    for r in replaces:
        parent_code = re.sub(r[0], r[1], t.code)
        try:
            if parent_code != t.code:
                parent = Term.objects.get(code=parent_code)
                break
        except Term.DoesNotExist:
            if debug:
                print 'not exist', parent_code, t.code
            continue
        except Term.MultipleObjectsReturned:
            parent = Term.objects.filter(code=parent_code)[0]
    return parent
