# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def create_relation_types(apps, schema_editor):
    Relation = apps.get_model("anatomy_tagging", "Relation")
    RelationType = apps.get_model("anatomy_tagging", "RelationType")

    unique_names = set([r.name for r in Relation.objects.all()])
    for name in unique_names:
        RelationType.objects.get_or_create(identifier=name, source='wikipedia')


def assign_proper_relation_types(apps, schema_editor):
    Relation = apps.get_model("anatomy_tagging", "Relation")
    RelationType = apps.get_model("anatomy_tagging", "RelationType")
    relation_types = {rt.identifier: rt for rt in RelationType.objects.all()}
    for rel in Relation.objects.all():
        rel.type = relation_types[rel.name]
        rel.save()


class Migration(migrations.Migration):

    dependencies = [
        ('anatomy_tagging', '0008_auto_relation_type'),
    ]

    operations = [
        migrations.RunPython(create_relation_types),
        migrations.RunPython(assign_proper_relation_types),
    ]
