# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('anatomy_tagging', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='term',
            name='body_part',
            field=models.CharField(default=None, max_length=2, null=True, choices=[(b'H', b'Head - Hlava'), (b'N', b'Neck - Krk'), (b'C', b'Chest - Hrudn\xc3\xad ko\xc5\xa1'), (b'A', b'Abdomen - B\xc5\x99icho'), (b'P', b'Pelvis - P\xc3\xa1nev'), (b'UE', b'Upper Ext. - Horn\xc3\xad kon\xc4\x8detina'), (b'LE', b'Lower Ext. - Doln\xc3\xad kon\xc4\x8detina')]),
            preserve_default=True,
        ),
    ]
