# -*- coding: utf-8 -*-
from collections import defaultdict, deque
from django.db import models
from django.db.models import Count
from django.db.models import Q
from django.template.defaultfilters import slugify
import json as simplejson
import re


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
        if (bbox_dict is not None and
                (image_or_path.bbox_id is None or
                    'updated' in bbox_dict)):
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

    def prepare_related(self):
        return self.select_related('parent')

    def get_term_from_dict(self, path_dict, term_key='term'):
        term = None
        if (term_key in path_dict and
                path_dict[term_key] is not None):
            if isinstance(path_dict[term_key], dict) and 'id' in path_dict[term_key]:
                term = self.get(id=path_dict[term_key]['id'])
            elif isinstance(path_dict[term_key], dict) and 'code' in path_dict[term_key]:
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
    fma_id = models.IntegerField(default=-1)
    name_cs = models.TextField(max_length=200)
    name_en = models.TextField(max_length=200)
    name_la = models.TextField(max_length=200)
    body_part = models.CharField(
        max_length=10,
        default='',
        null=True
    )
    system = models.CharField(
        max_length=30,
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
        return u'{0} ({1})'.format(self.name_la, self.slug)

    def to_serializable(self, subterm=False, without_parent=False):
        obj = {
            'id': self.id,
            'code': self.code if self.code != "" else self.slug,
            'slug': self.slug,
            'name_la': self.name_la,
            'name_cs': self.name_cs,
            'name_en': self.name_en,
            'body_part': self.body_part,
            'system': self.system,
            'fma_id': self.fma_id,
        }
        if not subterm and not without_parent and self.parent is not None:
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


class RelationTypeManager(models.Manager):

    def prepare_related(self):
        return self.prefetch_related('synonyms')

    def make_synonyms(self, first, second):
        first_synonyms = list(first.synonyms.all()) + [first]
        second_synonyms = list(second.synonyms.all()) + [second]
        for f in first_synonyms:
            for s in second_synonyms:
                f.synonyms.add(s)

    def from_identifier(self, identifier, source=None):
        if source is not None:
            return self.get_or_create(identifier=identifier, source=source)[0]
        else:
            found = list(self.filter(identifier=identifier))
            if len(found) == 0:
                raise Exception('There is no relation type of the given identifier {}.'.format(identifier))
            elif len(found) > 1:
                raise Exception('There are multiple relation types of the given identifier {}.'.format(identifier))
            return found[0]


class RelationType(models.Model):

    DEFAULT_QUESTION_CS = simplejson.dumps({
        't2ts': u'Chybí text otázky {}',
        'ts2t': u'Chybí text otázky {}',
    }, sort_keys=True)

    DEFAULT_QUESTION_EN = simplejson.dumps({
        't2ts': u'Question text missing {}',
        'ts2t': u'Question text missing {}',
    }, sort_keys=True)

    identifier = models.CharField(max_length=255)
    source = models.CharField(max_length=255)
    synonyms = models.ManyToManyField('self')
    ready = models.BooleanField(default=False)
    name_en = models.CharField(max_length=255, null=True)
    name_cs = models.CharField(max_length=255, null=True)
    display_priority = models.IntegerField(default=0)
    question_cs = models.TextField(default=DEFAULT_QUESTION_CS)
    question_en = models.TextField(default=DEFAULT_QUESTION_EN)

    objects = RelationTypeManager()

    def to_serializable(self, nested=False):
        result = {
            'id': self.id,
            'identifier': self.identifier,
            'source': self.source,
            'ready': self.ready,
            'name_en': self.name_en,
            'name_cs': self.name_cs,
            'display_priority': self.display_priority,
            'question_en': simplejson.loads(self.question_en),
            'question_cs': simplejson.loads(self.question_cs),
        }
        if not nested:
            result['synonyms'] = [rt.id for rt in self.synonyms.all()]
            if len(result['synonyms']) == 0:
                del result['synonyms']
        return result

    def __unicode__(self):
        return '{}: {}'.format(self.source, self.identifier)


class RelationManager(models.Manager):

    def get_tree(self, relation_type):
        rtype_ids = {relation_type.pk} | {t.pk for t in relation_type.synonyms.all()}
        by_id = {}
        by_term1 = defaultdict(list)
        for relation in self.filter(type_id__in=rtype_ids):
            by_id[relation.pk] = relation.to_serializable()
            if relation.term1_id is not None:
                by_term1[relation.term1_id].append(relation.pk)
            else:
                by_term1[relation.text1].append(relation.pk)
        for rel_id, rel_data in by_id.items():
            if rel_data['term2'] is None:
                children = by_term1[rel_data['text2']]
            else:
                children = by_term1[rel_data['term2']['id']]
            rel_data['children'] = children
            for child_id in children:
                child = by_id[child_id]
                if 'parent_ids' in child:
                    child['parent_ids'].append(rel_id)
                else:
                    child['parent_ids'] = [rel_id]
        previous = None
        previous_to_process = None
        next_to_process = None
        for rel_id, rel_data in by_id.items():
            if 'parent_id' in rel_data:
                continue
            to_visit = deque([rel_id])
            while len(to_visit) > 0:
                current = by_id[to_visit.popleft()]
                if 'next' in current:
                    raise Exception('There is a cycle in the graph.')
                if current['state'] == Relation.STATE_UNKNOWN:
                    if previous_to_process is not None:
                        previous_to_process['next_to_process'] = current['id']
                    else:
                        next_to_process = current['id']
                    previous_to_process = current
                if previous is not None:
                    current['previous'] = previous['id']
                    previous['next'] = current['id']
                previous = current
        return by_id, next_to_process

    def prepare_related(self):
        return self.select_related('term1', 'term2', 'term1__parent', 'term2__parent', 'type')


class Relation(models.Model):

    STATE_UNKNOWN = 'unknown'
    STATE_VALID = 'valid'
    STATE_INVALID = 'invalid'

    STATES = {
        'u': STATE_UNKNOWN,
        'v': STATE_VALID,
        'i': STATE_INVALID,
    }

    term1 = models.ForeignKey(Term, null=True, blank=True, related_name='term1')
    text1 = models.TextField()
    term2 = models.ForeignKey(Term, null=True, blank=True, related_name='term2')
    text2 = models.TextField(blank=True)
    type = models.ForeignKey(RelationType, null=True, blank=True, related_name='relations')
    state = models.CharField(max_length=1, choices=sorted(STATES.items()), default='u')
    labels = models.TextField(null=True, blank=True, default=None)

    objects = RelationManager()

    def to_serializable(self):
        obj = {
            'id': self.id,
            'name': self.type.identifier,
            'term1': to_serializable_or_none(self.term1, without_parent=True),
            'term2': to_serializable_or_none(self.term2, subterm=False),
            'text1': self.text1,
            'text2': self.text2,
            'type': self.type.to_serializable(nested=True),
            'state': Relation.STATES[self.state],
        }
        if self.labels:
            obj['labels'] = sorted(self.labels.split('|'))
        return obj

    def __unicode__(self):
        return u'{0}( {1}, {2})'.format(self.type.identifier, self.term1, self.term2)


def to_serializable_or_none(obj, **kwargs):
    return obj.to_serializable(**kwargs) if obj is not None else None


def canonical_term_name(name):
    canonical_name = re.sub('[\(\)]', '', name)
    canonical_name = re.sub(r'(\S)([-])(\S)', r'\1 \2 \3', canonical_name, re.UNICODE)
    canonical_name = re.sub(r',(\S)', r', \1', canonical_name, re.UNICODE)
    parts = '; '.join(p.strip() for p in canonical_name.split(';')).split(' ')
    canonical_name = ' '.join([_make_canonical_term_name_part(p.strip()) for p in parts]).replace(' A ', ' a ').replace(' S ', ' s ')
    canonical_name = re.sub(r' V (\w)', r' v \1', canonical_name, re.UNICODE)
    return canonical_name


def _make_canonical_term_name_part(value):
    if _is_roman_number(value) or _is_location(value):
        return value.upper()
    if _is_name(value):
        return '\''.join(p.title() if i == 0 else p for i, p in enumerate(value.split('\'')))
    filtered = ''.join(re.findall("\w+", value, flags=re.UNICODE))
    if filtered.lower() in ['vb', 'va', 'vc']:
        return value.lower().replace('v', 'V')
    if filtered.lower() in ['co']:
        return value.lower().replace('c', 'C')
    letters = {l for l in ''.join(re.findall("[^\W\d_]+", value, flags=re.UNICODE)).lower()}
    if letters == {'t', 'h'}:
        return re.sub(r'([^\d]|^)th', r'\1Th', value.lower(), re.UNICODE)
    return value.lower()


def _is_roman_number(value):
    value = value.lower()
    letters = {l for l in ''.join(re.findall("[^\W\d_]+", value, flags=re.UNICODE))}
    if letters <= {u'i', u'v', u'x'}:
        return True
    else:
        return False


def _is_location(value):
    filtered = ''.join(re.findall("\w+", value, flags=re.UNICODE))
    if len(filtered) == 1:
        return True
    letters = {l for l in ''.join(re.findall("[^\W\d_]+", value, flags=re.UNICODE)).lower()}
    if letters == {'t', 'h'}:
        return False
    return bool(re.search(r'\d', value))


def _is_name(value):
    value_lower = value.lower().strip(';')
    if any([value_lower.endswith(ext) for ext in ['ovo', u'ův', 'ova', 'ovi', 'ovy']]) or value_lower.endswith('\'s'):
        return True
    if value_lower in ['sorgius']:
        return True
    return False
