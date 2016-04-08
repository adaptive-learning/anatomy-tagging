# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('anatomy_tagging', '0006_term_system'),
    ]

    operations = [
        migrations.CreateModel(
            name='Relation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('text1', models.TextField()),
                ('text2', models.TextField()),
                ('name', models.TextField(max_length=10)),
                ('term1', models.ForeignKey(related_name='term1', to='anatomy_tagging.Term', null=True)),
                ('term2', models.ForeignKey(related_name='term2', to='anatomy_tagging.Term', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
