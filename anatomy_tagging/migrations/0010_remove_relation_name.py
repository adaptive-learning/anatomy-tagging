# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('anatomy_tagging', '0009_relation_names_to_types'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='relation',
            name='name',
        ),
    ]
