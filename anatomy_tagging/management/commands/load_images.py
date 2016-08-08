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
            try:
                file_name = os.path.basename(file_path)
                image = Image.objects.get(filename_slug=slugify(file_name)[:50])
                self.update_image(image, file_path)
            except Image.DoesNotExist:
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

    def get_paths_from_svg_file(self, file_path):
        map_dom = minidom.parse(file_path)
        paths = map_dom.getElementsByTagName(
            'path') + map_dom.getElementsByTagName(
            'ellipse') + map_dom.getElementsByTagName(
            'polyline') + map_dom.getElementsByTagName(
            'line')
        return paths

    def update_image(self, image, file_path):
        self.fix_gradients(image, file_path)
        paths = self.get_paths_from_svg_file(file_path)
        path_objects = []
        current_paths = Path.objects.filter(image=image)
        paths_dict = dict([(path.d, path) for path in current_paths])
        for path in paths:
            path_object = self.path_elem_to_object(path.attributes, image)
            if path_object.d in paths_dict:
                del paths_dict[path_object.d]
            else:
                path_objects.append(path_object)
        to_add = len(path_objects)
        to_remove = len(paths_dict.keys())
        if to_add + to_remove > 0:
            print ('updating image: ' + image.filename +
                   ' with %s elements') % len(paths)
            print "Objects to add:", to_add
            print "Objects to remove", to_remove
            print "Objects unchanged", len(current_paths) - to_remove
            # raw_input("Press enter to continue")
            Path.objects.bulk_create(path_objects)
            current_paths.filter(
                id__in=[path.id for path in paths_dict.values()]).delete()

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
        image = Image(
            filename=file_name,
            name_cs=file_name.replace('.svg', ''),
            filename_slug=slugify(file_name)[:50],
            category=category,
        )
        image.save()
        paths = self.get_paths_from_svg_file(file_path)
        path_objects = []
        print 'updating image: ' + file_name + ' with %s elements' % len(paths)
        for path in paths:
            path_object = self.path_elem_to_object(path.attributes, image)
            path_objects.append(path_object)
        Path.objects.bulk_create(path_objects)
        self.fix_gradients(image, file_path)

    def path_elem_to_object(self, attributes, image):
        stroke_width = 0
        if 'd' in attributes.keys():
            d = attributes['d'].value
            if 'z' not in d and 'Z' not in d:
                stroke_width = 1
        elif 'points' in attributes.keys():
            d = self.create_path_from_polyline(attributes)
            stroke_width = 2
        elif 'cx' in attributes.keys():
            d = self.create_path_from_ellipse(attributes)
            stroke_width = 2
        else:
            d = self.create_path_from_line(attributes)
            stroke_width = 2
        path_object = Path(
            image=image,
            opacity=self.get_attr_value(attributes, 'opacity', 1),
            color=self.get_attr_value(attributes, 'fill', 1),
            stroke=self.get_attr_value(attributes, 'stroke', None),
            stroke_width=self.get_attr_value(attributes, 'stroke-width', stroke_width),
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

    def create_path_from_polyline(self, attributes):
        path = 'M' + attributes['points'].value.strip().replace(" ", " L")
        print path
        return path

    def create_path_from_ellipse(self, attributes):
        cx = attributes['cx'].value
        cy = attributes['cy'].value
        ry = attributes['ry'].value
        rx = attributes['rx'].value
        path = "M" + str(float(cx) - float(rx)) + "," + cy
        path += "a" + rx + "," + ry + " 0 1,0 " + str(2 * float(rx)) + ",0"
        path += "a" + rx + "," + ry + " 0 1,0 " + str(-2 * float(rx)) + ",0"
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
