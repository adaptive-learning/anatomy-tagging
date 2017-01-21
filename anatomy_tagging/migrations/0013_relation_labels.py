# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('anatomy_tagging', '0012_relation_state'),
    ]

    operations = [
        migrations.AddField(
            model_name='relation',
            name='labels',
            field=models.TextField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='relation',
            name='state',
            field=models.CharField(default=b'u', max_length=1, choices=[(b'i', b'invalid'), (b'u', b'unknown'), (b'v', b'valid')]),
            preserve_default=True,
        ),
    ]
