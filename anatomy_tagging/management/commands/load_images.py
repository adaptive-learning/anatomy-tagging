# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from anatomy_tagging import settings
from xml.dom import minidom
import os
from anatomy_tagging.models import Image, Path, Category
from optparse import make_option
from django.template.defaultfilters import slugify
import csv


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
        self.add_folder(settings.MEDIA_DIR + self.IMAGES_DIR)
        self.load_csv(settings.MEDIA_DIR + self.IMAGES_DIR + 'images.csv')

    def add_folder(self, folder_path):
        for f in sorted(os.listdir(folder_path)):
            folder_name = os.path.basename(folder_path)
            child_path = os.path.join(folder_path, f)
            category = Category.objects.get_by_name(folder_name)
            if f.endswith('.svg'):
                try:
                    Image.objects.get(filename=f)
                except Image.DoesNotExist:
                    self.upload_image(child_path, category)
            elif os.path.isdir(child_path):
                self.add_folder(child_path)

    def upload_image(self, file_path, category):
        file_name = os.path.basename(file_path)
        map_dom = minidom.parse(file_path)
        image = Image(
            filename=file_name,
            name_cs=file_name.replace('.svg', ''),
            filename_slug=slugify(file_name),
            category=category,
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

    def load_csv(self, file_path):
        with open(file_path, 'rb') as csvfile:
            terms_reader = csv.reader(csvfile, delimiter=',')
            next(terms_reader, None)  # skip the headers
            for row in terms_reader:
                if row[6] == '1' and row[2] != '':
                    images = Image.objects.filter(filename__startswith=row[2])
                    for image in images:
                        if row[7] != '':
                            name = unicode(row[7], 'utf-8')
                        else:
                            name = image.filename.replace('.svg', '')
                        textbook_page = int(row[1])
                        body_part = row[8]
                        if (image.name_cs != name or
                                image.body_part != body_part or (
                                image.textbook_page != textbook_page and
                                textbook_page is not None)):
                            image.name_cs = name
                            image.body_part = body_part
                            image.textbook_page = textbook_page
                            image.save()
                            print 'Updated:', image
