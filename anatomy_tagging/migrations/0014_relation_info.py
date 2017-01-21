# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('anatomy_tagging', '0013_relation_labels'),
    ]

    operations = [
        migrations.AddField(
            model_name='relationtype',
            name='display_priority',
            field=models.IntegerField(default=0),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='relationtype',
            name='name_cs',
            field=models.CharField(max_length=255, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='relationtype',
            name='name_en',
            field=models.CharField(max_length=255, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='relationtype',
            name='question_cs',
            field=models.TextField(default=b'{"t2ts": "Chyb\\u00ed text ot\\u00e1zky {}", "ts2t": "Chyb\\u00ed text ot\\u00e1zky {}"}'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='relationtype',
            name='question_en',
            field=models.TextField(default=b'{"t2ts": "Question text missing {}", "ts2t": "Question text missing {}"}'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='relationtype',
            name='ready',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
