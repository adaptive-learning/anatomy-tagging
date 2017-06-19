# -*- coding: utf-8 -*-
from anatomy_tagging.models import Relation
from collections import defaultdict
from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):

    @transaction.atomic()
    def handle(self, *args, **options):
        groupped = defaultdict(list)
        for rel in Relation.objects.all():
            groupped[rel.type_id, rel.term1_id, rel.term2_id].append(rel)
        groupped = {key: rels for key, rels in groupped.items() if len(rels) > 1}
        for rels in groupped.values():
            keep = [rel for rel in rels if rel.state == 'v']
            if len(keep) == 0:
                keep = [rel for rel in rels if rel.state == 'u']
            keep = keep[0] if len(keep) > 0 else rels[0]
            for to_delete in [rel for rel in rels if rel.pk != keep.pk]:
                to_delete.delete()
