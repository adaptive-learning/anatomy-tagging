# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def set_wikipedia_relations_ready(apps, schema_editor):
    RelationType = apps.get_model("anatomy_tagging", "RelationType")
    RelationType.objects.filter(source='wikipedia').update(ready=True)


class Migration(migrations.Migration):

    dependencies = [
        ('anatomy_tagging', '0015_fill_relation_type_info'),
    ]

    operations = [
        migrations.RunPython(set_wikipedia_relations_ready),
    ]
