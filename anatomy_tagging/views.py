# -*- coding: utf-8 -*-
from django.shortcuts import render_to_response
from models import Term, Path, Image, Bbox
from django.http import HttpResponse
from django.db import connection
import json as simplejson
from django.shortcuts import get_object_or_404
from django.conf import settings


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
        "/static/js/bbox.js",
    ]
    c = {
        'js_files': [f + '?hash=' + settings.HASH for f in js_files],
        'ON_PRODUCTION': settings.ON_PRODUCTION,
    }
    request.META["CSRF_COOKIE_USED"] = True
    return render_to_response('home.html', c)


def images_json(request):
    images = Image.objects.all().select_related('bbox', 'category')
    counts = Image.objects.get_counts()
    json = {
        'images': [i.to_serializable() for i in images],
    }
    for i in json['images']:
        i.update(counts[i['id']])
    return render_json(request, json)


def image(request, filename_slug):
    c = {
        'filename_slug': filename_slug,
        'filename': filename_slug,
    }
    return render_to_response('image.html', c)


def update_term(request):
    if request.body:
        data = simplejson.loads(request.body)
        term = Term.objects.get(id=data['id'])
        term.name_la = data['name_la']
        term.name_en = data['name_en']
        term.body_part = data['body_part']
        term.parent = Term.objects.get_term_from_dict(data, 'parent')
        term.save()
        response = {
            'type': 'success',
            'msg': u'Změny byly uloženy',
        }
    return render_json(request, response)


def image_update(request):
    if request.body:
        data = simplejson.loads(request.body)
        image = get_object_or_404(Image, filename_slug=data['image']['filename_slug'])
        image.name_cs = data['image']['name_cs']
        image.name_en = data['image']['name_en']
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
        response = {
            'type': 'success',
            'msg': u'Změny byly uloženy',
        }
    return render_json(request, response)


def image_json(request, filename_slug):
    image = get_object_or_404(Image, filename_slug=filename_slug)
    paths = Path.objects.filter(image=image).select_related('term', 'bbox')
    json = {
        'image': image.to_serializable(),
        'paths': [p.to_serializable() for p in paths if p.term is None or p.term.code != 'too-small'],
    }
    return render_json(request, json)


def terms(request, filename_slug=None):
    terms = Term.objects.exclude(slug__in=['too-small', 'no-practice'])
    if filename_slug is not None and filename_slug != '':
        image = get_object_or_404(Image, filename_slug=filename_slug)
        paths = Path.objects.filter(image=image).select_related('term')
        print [p.term.name_la for p in paths if p.term_id is not None]
        terms = terms.filter(id__in=[p.term_id for p in paths if p.term_id is not None])

    terms = terms.select_related('parent')
    json = [t.to_serializable() for t in terms]
    return render_json(request, json)


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
