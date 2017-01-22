# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def set_wikipedia_relations_valid(apps, schema_editor):
    Relation = apps.get_model("anatomy_tagging", "Relation")
    Relation.objects.filter(type__identifier__in=[
        'action',
        'antagonist',
        'artery',
        'bone',
        'cranial fossa',
        'insertion',
        'nerve',
        'nerves',
        'origin',
        'vessels'
    ]).update(state='v')


class Migration(migrations.Migration):

    dependencies = [
        ('anatomy_tagging', '0016_wikipedia_relations_ready'),
    ]

    operations = [
        migrations.RunPython(set_wikipedia_relations_valid),
    ]
