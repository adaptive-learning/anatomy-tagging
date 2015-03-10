# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('anatomy_tagging', '0003_auto_20150307_0821'),
    ]

    operations = [
        migrations.AddField(
            model_name='image',
            name='body_part',
            field=models.CharField(default=b'', max_length=10, null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='term',
            name='body_part',
            field=models.CharField(default=b'', max_length=10, null=True),
            preserve_default=True,
        ),
    ]
