# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('anatomy_tagging', '0007_relation'),
    ]

    operations = [
        migrations.CreateModel(
            name='RelationType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('identifier', models.CharField(max_length=255)),
                ('source', models.CharField(max_length=255)),
                ('synonyms', models.ManyToManyField(related_name='synonyms_rel_+', to='anatomy_tagging.RelationType')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='relation',
            name='type',
            field=models.ForeignKey(related_name='relations', blank=True, to='anatomy_tagging.RelationType', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='relation',
            name='term1',
            field=models.ForeignKey(related_name='term1', blank=True, to='anatomy_tagging.Term', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='relation',
            name='term2',
            field=models.ForeignKey(related_name='term2', blank=True, to='anatomy_tagging.Term', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='relation',
            name='text2',
            field=models.TextField(blank=True),
            preserve_default=True,
        ),
    ]
