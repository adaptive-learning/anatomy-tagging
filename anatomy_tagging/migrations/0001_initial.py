# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Bbox',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('x', models.IntegerField(default=0)),
                ('y', models.IntegerField(default=0)),
                ('width', models.IntegerField()),
                ('height', models.IntegerField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('parent', models.ForeignKey(to='anatomy_tagging.Category', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Image',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('textbook_page', models.IntegerField(null=True)),
                ('filename', models.TextField(unique=True, max_length=200)),
                ('filename_slug', models.SlugField(unique=True, max_length=200)),
                ('name_cs', models.TextField(max_length=200, null=True)),
                ('name_en', models.TextField(max_length=200, null=True)),
                ('bbox', models.ForeignKey(to='anatomy_tagging.Bbox', null=True)),
                ('category', models.ForeignKey(to='anatomy_tagging.Category', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Path',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('d', models.TextField()),
                ('color', models.TextField(max_length=10)),
                ('stroke', models.TextField(max_length=10, null=True)),
                ('stroke_width', models.FloatField()),
                ('opacity', models.FloatField()),
                ('bbox', models.ForeignKey(to='anatomy_tagging.Bbox', null=True)),
                ('image', models.ForeignKey(to='anatomy_tagging.Image')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Term',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('slug', models.SlugField(unique=True, max_length=200)),
                ('code', models.TextField(max_length=200)),
                ('name_cs', models.TextField(max_length=200)),
                ('name_en', models.TextField(max_length=200)),
                ('name_la', models.TextField(max_length=200)),
                ('parent', models.ForeignKey(to='anatomy_tagging.Term', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='path',
            name='term',
            field=models.ForeignKey(to='anatomy_tagging.Term', null=True),
            preserve_default=True,
        ),
    ]
