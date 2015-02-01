# -*- coding: utf-8 -*-
from django.shortcuts import render_to_response
from models import Term, Path, Image
from django.http import HttpResponse
import json as simplejson
from django.shortcuts import get_object_or_404


def home(request):
    c = {
        'images': Image.objects.all(),
    }
    return render_to_response('home.html', c)


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
        image.x = int(data['image']['x'])
        image.x = int(data['image']['x'])
        image.width = int(data['image']['width'])
        image.height = int(data['image']['height'])
        image.save()
        for path_dict in data['paths']:
            term = None
            path = Path.objects.get(id=path_dict['id'])
            if ('term' in path_dict and
                    path_dict['term'] is not None and
                    'code' in path_dict['term']):
                term = Term.objects.get(code=path_dict['term']['code'])
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
    terms = Term.objects.all()
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
