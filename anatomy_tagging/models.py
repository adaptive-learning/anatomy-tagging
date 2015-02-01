from django.db import models


class Category(models.Model):
    parent = models.ForeignKey('self', null=True)


class Image(models.Model):
    category = models.ForeignKey(Category, null=True)
    x = models.IntegerField(default=0)
    y = models.IntegerField(default=0)
    width = models.IntegerField()
    height = models.IntegerField()
    textbook_page = models.IntegerField(null=True)
    filename = models.TextField(max_length=200)
    filename_slug = models.SlugField(max_length=200, db_index=True)
    name_cs = models.TextField(null=True, max_length=200)
    name_en = models.TextField(null=True, max_length=200)

    @property
    def get_paths_count(self):
        return Path.objects.filter(
            image=self.id
        ).exclude(
            term=Term.objects.get(slug='no-practice')
        ).exclude(
            term=Term.objects.get(slug='too-small')
        ).count()

    @property
    def get_untagged_paths_count(self):
        return Path.objects.filter(image=self.id, term=None).count()

    def __unicode__(self):
        return u'{0} ({1})'.format(self.name_cs, self.filename)

    def to_serializable(self):
        return {
            'filename': self.filename,
            'filename_slug': self.filename_slug,
            'name_cs': self.name_cs,
            'name_en': self.name_en,
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height,
        }


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

    def __unicode__(self):
        return u'{0} ({1})'.format(self.name_cs, self.slug)

    def to_serializable(self):
        return {
            'code': self.code,
            'name_cs': self.name_cs,
            'name_en': self.name_en,
            'name_la': self.name_la,
        }


class Path(models.Model):
    d = models.TextField()
    color = models.TextField(max_length=10)
    opacity = models.FloatField()
    term = models.ForeignKey(Term, null=True)
    image = models.ForeignKey(Image)

    def to_serializable(self):
        return {
            'id': self.id,
            'color': self.color,
            'opacity': self.opacity,
            'term': self.term.to_serializable() if not self.term is None else None,
            'd': self.d,
        }
