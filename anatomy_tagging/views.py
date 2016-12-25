# -*- coding: utf-8 -*-
from anatomy_tagging.management.commands.scrape_wiki import Command as WikiCommand, WIKI_PAGE_MUSCLES
from anatomy_tagging.management.commands.load_structured_fma import Command as FMACommand
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.core import management
from django.core.management.base import CommandError
from django.db import connection
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import render_to_response
from models import Term, Path, Image, Bbox, Relation, RelationType
import json as simplejson
import os


@staff_member_required
def home(request):
    js_files = [
        "/static/lib/jquery-1.11.0.js",
        "/static/lib/angular-1.2.9/angular.js",
        "/static/lib/angular-1.2.9/angular-cookies.js",
        "/static/lib/angular-1.2.9/angular-route.js",
        "/static/lib/ui-bootstrap.min.js",
        "/static/lib/ui-bootstrap-tpls.min.js",
        "/static/lib/raphael.js",
        "/static/lib/raphael.pan-zoom.js",
        "/static/lib/angular-slugify.js",
        "/static/lib/simplify.js",
        "/static/lib/roundProgress.js",
        "/static/js/app.js",
        "/static/js/controllers.js",
        "/static/js/directives.js",
        "/static/js/services.js",
        "/static/js/filters.js",
        "/static/js/bbox.js",
    ]
    c = {
        'js_files': [f + '?hash=' + settings.HASH for f in js_files],
        'ON_PRODUCTION': settings.ON_PRODUCTION,
    }
    request.META["CSRF_COOKIE_USED"] = True
    return render_to_response('home.html', c)


@staff_member_required
def images_json(request):
    images = Image.objects.all().select_related('bbox', 'category')
    json = {
        'images': [i.to_serializable() for i in images],
    }
    if 'omit_counts' not in request.GET:
        counts = Image.objects.get_counts()
        for i in json['images']:
            if i['id'] in counts:
                i.update(counts[i['id']])
    return render_json(request, json)


@staff_member_required
def image(request, filename_slug):
    c = {
        'filename_slug': filename_slug,
        'filename': filename_slug,
    }
    return render_to_response('image.html', c)


@staff_member_required
def update_term(request):
    if request.body:
        data = simplejson.loads(request.body)
        term = Term.objects.get(id=data['id'])
        term.name_la = data['name_la']
        term.name_en = data['name_en']
        term.name_cs = data['name_cs']
        term.body_part = data['body_part']
        term.system = data['system']
        term.parent = Term.objects.get_term_from_dict(data, 'parent')
        term.save()
        response = {
            'type': 'success',
            'msg': u'Změny byly uloženy',
        }
    return render_json(request, response)


@staff_member_required
def merge_terms(request):
    if request.body:
        data = simplejson.loads(request.body)
        term_to_be_removed = Term.objects.get(id=data['term1']['id'])
        term_survival = Term.objects.get(id=data['term2']['id'])
        paths = Path.objects.filter(
            term=term_to_be_removed).select_related('image')
        for p in paths:
            p.term = term_survival
            p.save()
        relations1 = Relation.objects.filter(term1=term_to_be_removed).select_related('term1')
        for p in relations1:
            p.term1 = term_survival
            p.save()
        relations2 = Relation.objects.filter(term2=term_to_be_removed).select_related('term2')
        for p in relations2:
            p.term2 = term_survival
            p.save()
        term_to_be_removed.delete()
        for image in list(set([p.image for p in paths])):
            try:
                export_image(image)
            except CommandError as e:
                response = {
                    'type': 'danger',
                    'msg': u'%s' % e,
                }
                return render_json(request, response)
        response = {
            'type': 'success',
            'msg': u'Změny byly uloženy',
        }
    return render_json(request, response)


@staff_member_required
def image_update(request):
    if request.body:
        data = simplejson.loads(request.body)
        image = get_object_or_404(Image, filename_slug=data['image']['filename_slug'])
        image.name_cs = data['image']['name_cs']
        image.name_en = data['image']['name_en']
        image.active = data['image']['active']
        try:
            image.textbook_page = int(data['image']['textbook_page'])
        except ValueError:
            image.textbook_page = None
        except TypeError:
            image.textbook_page = None
        Bbox.objects.add_to_image(image, data['image']['bbox'])
        image.save()
        paths_by_id = dict([
            (p.id, p) for p in
            Path.objects.filter(image=image.id).select_related('bbox')
        ])
        for path_dict in data['paths']:
            path = paths_by_id[path_dict['id']]
            # path = Path.objects.select_related('bbox').get(id=path_dict['id'])
            path_updated = Bbox.objects.add_to_path(path, path_dict['bbox'])
            term = Term.objects.get_term_from_dict(path_dict, 'term')
            if term is not None:
                if path.term_id != term.id:
                    path.term = term
                    path_updated = True
                if ((term.body_part is None or term.body_part == '') and
                        image.body_part != ''):
                    term.body_part = image.body_part
                    term.save()
            elif term is None and path.term is not None:
                path.term = None
                path_updated = True
            if path_updated:
                path.save()
        if data.get('export', False):
            try:
                export_image(image)
            except CommandError as e:
                response = {
                    'type': 'danger',
                    'msg': u'%s' % e,
                }
                return render_json(request, response)
        response = {
            'type': 'success',
            'msg': u'Změny byly uloženy',
        }
    return render_json(request, response)


def export_image(image):
    export_dir = os.path.join(settings.MEDIA_DIR, 'export')
    if not os.path.exists(export_dir):
            os.makedirs(export_dir)
    management.call_command(
        'export_flashcards',
        context=image.filename_slug,
        output=os.path.join(export_dir, 'image.json'),
        verbosity=0,
        interactive=False)


@staff_member_required
def image_json(request, filename_slug):
    image = get_object_or_404(Image, filename_slug=filename_slug)
    paths = Path.objects.filter(image=image).select_related('term', 'bbox')
    json = {
        'image': image.to_serializable(),
        'paths': [p.to_serializable() for p in paths],
    }
    return render_json(request, json)


@staff_member_required
def terms(request, filename_slug=None):
    terms = Term.objects.exclude(slug__in=['too-small', 'no-practice'])
    terms = terms.select_related('parent')
    if filename_slug == 'duplicate':
        terms = terms.order_by('name_la', '-id')
        paths = Path.objects.all().select_related('term')
        relations = Relation.objects.all().select_related('term1,term2')
        used_terms_ids = list(set(
            [p.term_id for p in paths if p.term_id is not None] +
            [r.term1_id for r in relations if r.term1_id is not None] +
            [r.term2_id for r in relations if r.term2_id is not None] +
            [r.term2.parent_id for r in relations if r.term2_id is not None]
        ))
        terms = [t for t in terms if t.id in used_terms_ids]
        term_dict = {}
        for t in terms:
            term_dict[t.name_la] = term_dict.get(t.name_la, 0) + 1
        terms = [t for t in terms if term_dict[t.name_la] > 1]
    elif filename_slug is not None and filename_slug != '':
        image = get_object_or_404(Image, filename_slug=filename_slug)
        paths = Path.objects.filter(image=image).select_related('term')
        terms = terms.filter(
            id__in=list(set([p.term_id for p in paths if p.term_id is not None]))
        ).order_by('-id')

    json = [t.to_serializable() for t in terms]

    if 'images' in request.GET:
        paths = Path.objects.exclude(
            term=None).exclude(
            term__slug__in=['too-small', 'no-practice']).select_related(
            'image', 'term')
        image_by_term = {}
        for p in paths:
            image_by_term[p.term.slug] = image_by_term.get(p.term.slug, [])
            image_by_term[p.term.slug].append(p.image.filename_slug)
        for t in json:
            images = image_by_term.get(t['slug'], None)
            if images is not None:
                t['images'] = list(set(images))

    if 'relations' in request.GET:
        relations = Relation.objects.all().select_related('term1', 'term1')
        relation_by_term = {}
        for r in relations:
            if r.term1 is not None and r.term2 is not None:
                relation_by_term[r.term1.slug] = relation_by_term.get(r.term1.slug, [])
                relation_by_term[r.term1.slug].append(r.term2.name_la)
                relation_by_term[r.term2.slug] = relation_by_term.get(r.term2.slug, [])
                relation_by_term[r.term2.slug].append(r.term1.name_la)
        for t in json:
            relations = relation_by_term.get(t['slug'], None)
            if relations is not None:
                t['relations'] = list(set(relations))
    if 'usedonly' in request.GET:
            json = [t for t in json if 'relations' in t or 'images' in t]
    return render_json(request, json)


@staff_member_required
def relations_json(request, source=None):
    if source.startswith('FMA_'):
        basename = os.path.join(settings.MEDIA_DIR, source.replace('FMA_', ''))
        if os.path.exists(basename + '.yaml'):
            filename = basename + '.yaml'
        else:
            filename = basename + '.json'
        raw_relations = FMACommand().get_relations(filename)
    else:
        raw_relations = WikiCommand().get_relations(source or WIKI_PAGE_MUSCLES)
    relations = [r.to_serializable() for r in Relation.objects.prepare_related().all()]
    json = {
        'raw': raw_relations,
        'relations': relations,
    }
    return render_json(request, json)


@staff_member_required
def relations_export(request, relation_type=None):
    export_dir = os.path.join(settings.MEDIA_DIR, 'export')
    if relation_type is not None and relation_type != '':
        file_name = 'image-' + relation_type + '.json'
    else:
        file_name = 'image-relations-flashcards.json'
    out_file = os.path.join(export_dir, file_name)
    management.call_command(
        'export_relations',
        relationtype=relation_type.replace(' ', '-'),
        output=out_file,
        verbosity=0,
        interactive=False)

    data = {}
    if 'empty' not in request.GET:
        with open(out_file, 'rb') as f:
            data = simplejson.load(f)
    return render_json(request, data)


@staff_member_required
def update_relations(request):
    if request.body:
        data = simplejson.loads(request.body)
        if len(data) > 0:
            Relation.objects.filter(
                term1=Term.objects.get_term_from_dict(data[0], 'term1')
            ).exclude(
                id__in=[r['id'] for r in data if 'id' in r],
            ).delete()
        for r_data in data:
            if 'id' in r_data:
                relation = Relation.objects.get(id=r_data['id'])
            else:
                relation = Relation()
            relation.text1 = r_data['text1']
            relation.text2 = r_data['text2']
            relation.type = RelationType.objects.from_identifier(
                identifier=r_data['name'],
                source=get_source(request),)
            relation.term1 = Term.objects.get_term_from_dict(r_data, 'term1')
            relation.term2 = Term.objects.get_term_from_dict(r_data, 'term2')
            add_fma_id(relation.term1, r_data.get('text1'))
            add_fma_id(relation.term2, r_data.get('text2'))
            relation.save()
        response = {
            'type': 'success',
            'msg': u'Změny byly uloženy',
        }
    return render_json(request, response)


def get_source(request):
    return {
        'FMA': 'fma',
        'List': 'wikipedia'
    }.get(request.GET.get('source', '').split('_')[0], 'unknown')


def add_fma_id(term, text):
    fmaid = None
    if len(text.split(':')) == 3:
        fmaid = text.split(':')[0].replace('FMA', '')

    if term is not None and fmaid is not None and term.fma_id == -1:
        try:
            term.fma_id = int(fmaid)
            term.save()
        except ValueError:
            pass


@staff_member_required
def render_json(request, json, status=None,):
    if 'html' in request.GET:
        return HttpResponse(
            content=simplejson.dumps(json),
            status=status,
        )

    if settings.DEBUG and 'sqldump' in request.GET:
        return HttpResponse(
            content=str(connection.queries),
            content_type='text/plain',
            status=status,
        )
    return JsonResponse(json)


class JsonResponse(HttpResponse):

    """
        JSON response
    """

    def __init__(self, content, content_type='application/json',
                 status=None):
        super(JsonResponse, self).__init__(
            content=simplejson.dumps(content),
            content_type=content_type,
            status=status,
        )
