# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('anatomy_tagging', '0005_image_active'),
    ]

    operations = [
        migrations.AddField(
            model_name='term',
            name='system',
            field=models.CharField(default=b'', max_length=30, null=True),
            preserve_default=True,
        ),
    ]
