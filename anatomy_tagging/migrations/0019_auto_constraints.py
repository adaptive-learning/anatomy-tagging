# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('anatomy_tagging', '0018_auto_composite_relation_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='term',
            name='body_part',
            field=models.CharField(default=b'', max_length=10, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='term',
            name='name_cs',
            field=models.TextField(max_length=200, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='term',
            name='name_en',
            field=models.TextField(max_length=200, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='term',
            name='name_la',
            field=models.TextField(max_length=200, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='term',
            name='parent',
            field=models.ForeignKey(blank=True, to='anatomy_tagging.Term', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='term',
            name='system',
            field=models.CharField(default=b'', max_length=30, null=True, blank=True),
            preserve_default=True,
        ),
    ]
