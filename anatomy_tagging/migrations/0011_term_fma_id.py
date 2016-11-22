# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('anatomy_tagging', '0010_remove_relation_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='term',
            name='fma_id',
            field=models.IntegerField(default=-1),
            preserve_default=True,
        ),
    ]
