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
    help = u"""Load images from svg files.
    If one argument is provided it is used as path to the image to be loaded"""
    option_list = BaseCommand.option_list + (
        make_option(
            '--delete',
            action='store_true',
            dest='delete',
            default=False,
            help='Delete images and paths at first',
        ),
    )
    IMAGES_DIR = '/svg/'

    def handle(self, *args, **options):
        if len(args) > 0:
            file_path = args[0]
            folder_name = file_path.split('/')[-2]
            category = Category.objects.get_by_name(folder_name)
            if options['delete']:
                self.delete_image(file_path)
            self.upload_image(file_path, category)
        else:
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
                    image = Image.objects.get(filename_slug=slugify(f)[:50])
                    self.update_image(image, child_path)
                except Image.DoesNotExist:
                    try:
                        image = Image.objects.get(filename=f)
                        self.update_image(image, child_path)
                    except Image.DoesNotExist:
                        self.upload_image(child_path, category)
            elif os.path.isdir(child_path):
                self.add_folder(child_path)

    def update_image(self, image, file_path):
        self.fix_gradients(image, file_path)

    def fix_gradients(self, image, file_path):
        map_dom = minidom.parse(file_path)
        gradients = map_dom.getElementsByTagName('radialGradient')
        for gradient in gradients:
            gradient_id = gradient.attributes['id'].value
            first_stop = gradient.getElementsByTagName('stop')[-1]
            first_stop_style = first_stop.attributes['style'].value
            first_stop_color = first_stop_style.replace('stop-color:', '')
            paths = Path.objects.filter(
                color='url(#%s)' % gradient_id,
                image=image)
            for path in paths:
                print 'updating gradients in image: ' + image.filename
                path.color = first_stop_color
                path.save()

    def delete_image(self, file_path):
        file_name = os.path.basename(file_path)
        try:
            image = Image.objects.get(filename=file_name)
            Path.objects.filter(image=image).delete()
            image.delete()
        except Image.DoesNotExist:
            pass

    def upload_image(self, file_path, category):
        file_name = os.path.basename(file_path)
        map_dom = minidom.parse(file_path)
        image = Image(
            filename=file_name,
            name_cs=file_name.replace('.svg', ''),
            filename_slug=slugify(file_name)[:50],
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
        self.fix_gradients(image, file_path)

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
