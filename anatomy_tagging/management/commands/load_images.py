# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from anatomy_tagging import settings
from xml.dom import minidom
from os import listdir
from anatomy_tagging.models import Image, Path
from optparse import make_option
from django.template.defaultfilters import slugify


class Command(BaseCommand):
    help = u"""Load images from svg files"""
    option_list = BaseCommand.option_list + (
        make_option(
            '--delete',
            action='store_true',
            dest='delete',
            default=False,
            help='Delete all images and paths at first',
        ),
    )
    IMAGES_DIR = '/svg/'

    def handle(self, *args, **options):
        if options['delete']:
            Image.objects.all().delete()
            Path.objects.all().delete()
        for f in sorted(listdir(settings.BASE_DIR + self.IMAGES_DIR)):
            if f.endswith('.svg'):
                self.upload_image(f)

    def upload_image(self, file_name):
        file_path = settings.BASE_DIR + self.IMAGES_DIR + file_name
        map_dom = minidom.parse(file_path)
        svg = map_dom.getElementsByTagName('svg')[0]
        image = Image(
            filename=file_name,
            filename_slug=slugify(file_name),
            height=int(svg.attributes['height'].value.replace('px', '').split('.')[0]),
            width=int(svg.attributes['width'].value.replace('px', '').split('.')[0]),
        )
        image.save()
        paths = map_dom.getElementsByTagName('path')
        path_objects = []
        print 'updating image: ' + file_name + ' with %s elements' % len(paths)
        for path in paths:
            if 'opacity' in path.attributes.keys():
                opacity = path.attributes['opacity'].value
            else:
                opacity = 1
            if 'fill' in path.attributes.keys():
                fill = path.attributes['fill'].value
            else:
                fill = 1
            path_object = Path(
                image=image,
                opacity=opacity,
                color=fill,
                d=path.attributes['d'].value,
            )
            path_objects.append(path_object)
        Path.objects.bulk_create(path_objects)
