# -*- coding: utf-8 -*-
from django.shortcuts import render_to_response
from models import Term, Path, Image, Bbox
from django.http import HttpResponse
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
        "/static/js/app.js",
        "/static/js/controllers.js",
        "/static/js/directives.js",
        "/static/js/services.js",
        "/static/js/bbox.js",
    ]
    c = {
        'images': Image.objects.all(),
        'js_files': [f + '?hash=' + settings.HASH for f in js_files]
    }
    request.META["CSRF_COOKIE_USED"] = True
    return render_to_response('home.html', c)


def images_json(request):
    images = Image.objects.all()
    json = {
        'images': [i.to_serializable() for i in images],
    }
    return JsonResponse(json)


def image(request, filename_slug):
    c = {
        'filename_slug': filename_slug,
        'filename': filename_slug,
    }
    return render_to_response('image.html', c)


def image_update(request):
    if request.body:
        data = simplejson.loads(request.body)
        image = get_object_or_404(Image, filename_slug=data['image']['filename_slug'])
        image.name_cs = data['image']['name_cs']
        image.name_en = data['image']['name_en']
        Bbox.objects.add_to_image(image, data['image']['bbox'])
        image.save()
        for path_dict in data['paths']:
            path = Path.objects.get(id=path_dict['id'])
            Bbox.objects.add_to_path(path, path_dict['bbox'])
            term = Term.objects.get_term_from_dict(path_dict)
            if term is not None:
                if path.term_id != term.id:
                    path.term = term
                    path.save()
            elif term is None and path.term is not None:
                path.term = None
                path.save()
        response = {
            'type': 'success',
            'msg': u'Změny byly uloženy',
        }
    return JsonResponse(response)


def image_json(request, filename_slug):
    image = get_object_or_404(Image, filename_slug=filename_slug)
    paths = Path.objects.filter(image=image)
    json = {
        'image': image.to_serializable(),
        'paths': [p.to_serializable() for p in paths if p.term is None or p.term.code != 'too-small'],
    }
    return JsonResponse(json)


def terms(request):
    terms = Term.objects.exclude(slug__in=['too-small', 'no-practice'])
    json = [t.to_serializable() for t in terms]
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
