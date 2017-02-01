# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('anatomy_tagging', '0017_wikipedia_relations_valid'),
    ]

    operations = [
        migrations.CreateModel(
            name='CompositeRelationType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('identifier', models.CharField(max_length=255)),
                ('ready', models.BooleanField(default=False)),
                ('name_en', models.CharField(max_length=255, null=True)),
                ('name_cs', models.CharField(max_length=255, null=True)),
                ('display_priority', models.IntegerField(default=0)),
                ('question_cs', models.TextField(default=b'{"t2ts": "Chyb\\u00ed text ot\\u00e1zky {}", "ts2t": "Chyb\\u00ed text ot\\u00e1zky {}"}')),
                ('question_en', models.TextField(default=b'{"t2ts": "Question text missing {}", "ts2t": "Question text missing {}"}')),
                ('definition', models.TextField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterField(
            model_name='relationtype',
            name='synonyms',
            field=models.ManyToManyField(related_name='synonyms_rel_+', to='anatomy_tagging.RelationType', blank=True),
            preserve_default=True,
        ),
    ]
