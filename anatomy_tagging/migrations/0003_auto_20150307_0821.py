# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('anatomy_tagging', '0002_term_body_part'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='name_cs',
            field=models.TextField(default=b'', max_length=200),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='category',
            name='name_en',
            field=models.TextField(default=b'', max_length=200),
            preserve_default=True,
        ),
    ]
