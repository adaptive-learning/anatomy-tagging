# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('anatomy_tagging', '0011_term_fma_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='relation',
            name='state',
            field=models.CharField(default=b'u', max_length=1, choices=[(b'u', b'Unknown'), (b'v', b'Valid'), (b'i', b'Invalid')]),
            preserve_default=True,
        ),
    ]
