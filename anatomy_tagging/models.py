# -*- coding: utf-8 -*-
from django.db import models
from django.template.defaultfilters import slugify
from django.db.models import Count
from django.db.models import Q


class CategoryManager(models.Manager):
    def get_by_name(self, name):
        try:
            cat = self.get(name_cs=name)
        except Category.DoesNotExist:
            cat = Category(
                name_cs=name,
            )
            cat.save()
        return cat


class Category(models.Model):
    parent = models.ForeignKey('self', null=True)
    name_cs = models.TextField(max_length=200, default="")
    name_en = models.TextField(max_length=200, default="")

    objects = CategoryManager()

    def __unicode__(self):
        return u'{0}'.format(self.name_cs)

    def to_serializable(self):
        return {
            'name_cs': self.name_cs,
            'name_en': self.name_en,
        }


class BboxManager(models.Manager):
    def add_to_image(self, image, bbox_dict):
        return self._add_to_image_or_path(image, bbox_dict)

    def add_to_path(self, path, bbox_dict):
        return self._add_to_image_or_path(path, bbox_dict)

    def _add_to_image_or_path(self, image_or_path, bbox_dict):
        if image_or_path.bbox_id is None and bbox_dict is not None:
            bbox = Bbox(
                x=int(bbox_dict['x']),
                y=int(bbox_dict['y']),
                width=int(bbox_dict['width']),
                height=int(bbox_dict['height']),
            )
            bbox.save()
            image_or_path.bbox = bbox
            return True


class Bbox(models.Model):
    x = models.IntegerField(default=0)
    y = models.IntegerField(default=0)
    width = models.IntegerField()
    height = models.IntegerField()

    objects = BboxManager()

    def __unicode__(self):
        return u'BBox[{0}, {1}, {2}, {3}]'.format(
            self.x, self.y, self.width, self.height)

    def to_serializable(self):
        return {
            'x': self.x,
            'y': self.y,
            'x2': self.x + self.width,
            'y2': self.y + self.height,
            'width': self.width,
            'height': self.height,
        }


class ImageManager(models.Manager):

    def get_counts(self):
        untagged_paths_count = Path.objects.filter(
            term=None
        ).values('image').annotate(Count('image'))
        untagged_paths_count = self.to_dict(untagged_paths_count)

        incomplete_terms_count = Path.objects.exclude(
            term=None,
        ).exclude(
            term__slug__in=['no-practice', 'too-small'],
        ).filter(
            Q(term__parent=None) |
            Q(term__body_part=None) |
            Q(term__body_part='') |
            Q(term__name_en=None) |
            Q(term__name_en='')
        ).values('image').annotate(Count('image'))

        incomplete_terms_count = self.to_dict(incomplete_terms_count)

        paths_count = Path.objects.exclude(
            term__slug='no-practice'
        ).exclude(
            term__slug='too-small'
        ).values('image').annotate(Count('image'))

        ret = dict([(c['image'], {
            'paths_count': c['image__count'],
            'untagged_paths_count': untagged_paths_count.get(c['image'], 0),
            'paths_progress': self.paths_progress(
                c['image__count'],
                untagged_paths_count.get(c['image'], 0)),
            'incomplete_terms_count': incomplete_terms_count.get(c['image'], 0),
            'terms_count': c['image__count'] - untagged_paths_count.get(c['image'], 0),
            'terms_progress': self.paths_progress(
                c['image__count'] - incomplete_terms_count.get(c['image'], 0),
                incomplete_terms_count.get(c['image'], 0)),
        }) for c in paths_count])
        return ret

    def to_dict(self, count):
        return dict([(c['image'], c['image__count']) for c in count])

    def paths_progress(self, paths_count, untagged_paths_count):
        if paths_count == 0:
            return 0
        return 100.0 * ((paths_count - untagged_paths_count) / (paths_count * 1.0))


class Image(models.Model):
    category = models.ForeignKey(Category, null=True)
    bbox = models.ForeignKey(Bbox, null=True)
    textbook_page = models.IntegerField(null=True)
    filename = models.TextField(max_length=200, unique=True)
    filename_slug = models.SlugField(
        max_length=200,
        db_index=True,
        unique=True)
    name_cs = models.TextField(null=True, max_length=200)
    name_en = models.TextField(null=True, max_length=200)
    body_part = models.CharField(
        max_length=10,
        default='',
        null=True
    )
    active = models.BooleanField(default=False)

    objects = ImageManager()

    def __unicode__(self):
        return u'{0} ({1})'.format(self.name_cs, self.filename)

    def to_serializable(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'filename_slug': self.filename_slug,
            'name_cs': self.name_cs,
            'name_en': self.name_en,
            'textbook_page': self.textbook_page,
            'bbox': to_serializable_or_none(self.bbox),
            'category': to_serializable_or_none(self.category),
            'active': self.active,
        }


class TermManager(models.Manager):
    def get_term_from_dict(self, path_dict, term_key='term'):
        term = None
        if (term_key in path_dict and
                path_dict[term_key] is not None):
            if 'id' in path_dict[term_key]:
                term = self.get(id=path_dict[term_key]['id'])
            elif 'code' in path_dict[term_key]:
                term = self.get(code=path_dict[term_key]['code'])
            elif (isinstance(path_dict[term_key], basestring) and
                    path_dict[term_key]):
                try:
                    term = self.select_related('bbox').get(name_la=path_dict[term_key])
                except Term.DoesNotExist:
                    term = Term(
                        name_la=path_dict[term_key],
                    )
                    term.save()
            return term


class Term(models.Model):
    HEAD = "H"
    NECK = "N"
    CHEST = "C"
    ABDOMEN = "A"
    PELVIS = "P"
    UPPER_EXT = "UE"
    LOWER_EXT = "LE"

    BODY_PARTS = (
        (HEAD, 'Head - Hlava'),
        (NECK, 'Neck - Krk'),
        (CHEST, 'Chest - Hrudní koš'),
        (ABDOMEN, 'Abdomen - Břicho'),
        (PELVIS, 'Pelvis - Pánev'),
        (UPPER_EXT, 'Upper Ext. - Horní končetina'),
        (LOWER_EXT, 'Lower Ext. - Dolní končetina'),
    )
    parent = models.ForeignKey('self', null=True)
    slug = models.SlugField(
        max_length=200,
        db_index=True,
        unique=True)
    code = models.TextField(max_length=200)
    name_cs = models.TextField(max_length=200)
    name_en = models.TextField(max_length=200)
    name_la = models.TextField(max_length=200)
    body_part = models.CharField(
        max_length=10,
        default='',
        null=True
    )

    objects = TermManager()

    # Overriding
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name_la)
            print self.slug
            while Term.objects.filter(slug=self.slug).exists():
                self.slug += '_dup'
        super(Term, self).save(*args, **kwargs)

    def __unicode__(self):
        return u'{0} ({1})'.format(self.name_cs, self.slug)

    def to_serializable(self, subterm=False):
        obj = {
            'id': self.id,
            'code': self.code if self.code != "" else self.slug,
            'name_la': self.name_la,
            'name_cs': self.name_cs,
            'name_en': self.name_en,
            'body_part': self.body_part,
        }
        if not subterm and self.parent is not None:
            obj['parent'] = self.parent.to_serializable(True)
        return obj


class Path(models.Model):
    d = models.TextField()
    color = models.TextField(max_length=10)
    stroke = models.TextField(max_length=10, null=True)
    stroke_width = models.FloatField()
    opacity = models.FloatField()
    term = models.ForeignKey(Term, null=True)
    image = models.ForeignKey(Image, db_index=True)
    bbox = models.ForeignKey(Bbox, null=True)

    def to_serializable(self):
        return {
            'id': self.id,
            'color': self.color,
            'stroke': self.stroke,
            'stroke_width': self.stroke_width,
            'opacity': self.opacity,
            'term': to_serializable_or_none(self.term),
            'd': self.d,
            'bbox': to_serializable_or_none(self.bbox),
        }


def to_serializable_or_none(obj):
    return obj.to_serializable() if obj is not None else None
