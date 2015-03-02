from django.db import models
from django.template.defaultfilters import slugify


class Category(models.Model):
    parent = models.ForeignKey('self', null=True)


class BboxManager(models.Manager):
    def add_to_image(self, image, bbox_dict):
        self._add_to_image_or_path(image, bbox_dict)

    def add_to_path(self, path, bbox_dict):
        self._add_to_image_or_path(path, bbox_dict)

    def _add_to_image_or_path(self, image_or_path, bbox_dict):
        if image_or_path.bbox is None and bbox_dict is not None:
            bbox = Bbox(
                x=int(bbox_dict['x']),
                y=int(bbox_dict['y']),
                width=int(bbox_dict['width']),
                height=int(bbox_dict['height']),
            )
            bbox.save()
            image_or_path.bbox = bbox


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


class Image(models.Model):
    category = models.ForeignKey(Category, null=True)
    bbox = models.ForeignKey(Bbox, null=True)
    textbook_page = models.IntegerField(null=True)
    filename = models.TextField(max_length=200, unique=True)
    filename_slug = models.SlugField(max_length=200, db_index=True, unique=True)
    name_cs = models.TextField(null=True, max_length=200)
    name_en = models.TextField(null=True, max_length=200)

    @property
    def progress(self):
        paths_count = self.paths_count
        untagged_paths_count = self.untagged_paths_count
        return (100.0 * (paths_count - untagged_paths_count)) / paths_count

    @property
    def paths_count(self):
        return Path.objects.filter(
            image=self.id
        ).exclude(
            term=Term.objects.get(slug='no-practice')
        ).exclude(
            term=Term.objects.get(slug='too-small')
        ).count()

    @property
    def untagged_paths_count(self):
        return Path.objects.filter(image=self.id, term=None).count()

    def __unicode__(self):
        return u'{0} ({1})'.format(self.name_cs, self.filename)

    def to_serializable(self):
        return {
            'filename': self.filename,
            'filename_slug': self.filename_slug,
            'name_cs': self.name_cs,
            'name_en': self.name_en,
            'bbox': self.bbox.to_serializable() if self.bbox is not None else None,
            'progress': self.progress,
            'paths_count': self.paths_count,
            'untagged_paths_count': self.untagged_paths_count,
        }


class TermManager(models.Manager):
    def get_term_from_dict(self, path_dict, term_key='term'):
        term = None
        if (term_key in path_dict and
                path_dict[term_key] is not None):
            if 'id' in path_dict[term_key]:
                term = self.get(id=path_dict[term_key]['id'])
            elif isinstance(path_dict[term_key], basestring) and path_dict[term_key]:
                try:
                    term = self.get(name_la=path_dict[term_key])
                except Term.DoesNotExist:
                    term = Term(
                        name_la=path_dict[term_key],
                    )
                    term.save()
            return term


class Term(models.Model):
    parent = models.ForeignKey('self', null=True)
    slug = models.SlugField(
        max_length=200,
        db_index=True,
        unique=True)
    code = models.TextField(max_length=200)
    name_cs = models.TextField(max_length=200)
    name_en = models.TextField(max_length=200)
    name_la = models.TextField(max_length=200)

    objects = TermManager()

    # Overriding
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name_la)
            print self.slug
            while Term.objects.filter(slug=self.slug).exists():
                self.slug += '_duplicate'
        super(Term, self).save(*args, **kwargs)

    def __unicode__(self):
        return u'{0} ({1})'.format(self.name_cs, self.slug)

    def to_serializable(self, subterm=False):
        obj = {
            'id': self.id,
            'code': self.code,
            'name_la': self.name_la,
            'name_cs': self.name_cs,
            'name_en': self.name_en,
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
            'term': self.term.to_serializable() if not self.term is None else None,
            'd': self.d,
            'bbox': self.bbox.to_serializable() if self.bbox is not None else None,
        }
