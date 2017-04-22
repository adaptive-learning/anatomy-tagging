# -*- coding: utf-8 -*-

from anatomy_tagging.models import CompositeRelationType
from django.core.management.base import BaseCommand, CommandError
from optparse import make_option


class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option(
            '--relation',
            dest='relation',
            type=str,
            default=None),
    )

    def handle(self, *args, **options):
        if options['relation'] is None:
            raise CommandError('There is no relation definition.')
        for term1, term2 in CompositeRelationType.objects.composite_relation_from_definition(options['relation']):
            name1 = term1.name_la if term1.name_la else term1.name_en
            name2 = term2.name_la if term2.name_la else term2.name_en
            print name1.encode('utf-8'), '---->', name2.encode('utf-8')
