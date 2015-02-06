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
        for f in sorted(listdir(settings.MEDIA_DIR + self.IMAGES_DIR)):
            if f.endswith('.svg'):
                try:
                    Image.objects.get(filename=f)
                except Image.DoesNotExist:
                    self.upload_image(f)

    def upload_image(self, file_name):
        file_path = settings.MEDIA_DIR + self.IMAGES_DIR + file_name
        map_dom = minidom.parse(file_path)
        image = Image(
            filename=file_name,
            filename_slug=slugify(file_name),
        )
        image.save()
        paths = map_dom.getElementsByTagName('path') + map_dom.getElementsByTagName('line')
        path_objects = []
        print 'updating image: ' + file_name + ' with %s elements' % len(paths)
        for path in paths:
            path_object = self.path_elem_to_object(path.attributes, image)
            path_objects.append(path_object)
        Path.objects.bulk_create(path_objects)

    def path_elem_to_object(self, attributes, image):
        if 'd' in attributes.keys():
            d = attributes['d'].value
        else:
            d = self.create_path_from_line(attributes)
        path_object = Path(
            image=image,
            opacity=self.get_attr_value(attributes, 'opacity', 1),
            color=self.get_attr_value(attributes, 'fill', 1),
            stroke=self.get_attr_value(attributes, 'stroke', None),
            stroke_width=self.get_attr_value(attributes, 'stroke-width', 0),
            d=d,
        )
        return path_object

    def get_attr_value(self, attributes, key, default):
        if key in attributes.keys():
            return attributes[key].value
        else:
            return default

    def create_path_from_line(self, attributes):
        path = "M" + attributes['x1'].value + ',' + attributes['y1'].value
        path += "L" + attributes['x2'].value + ',' + attributes['y2'].value
        return path
