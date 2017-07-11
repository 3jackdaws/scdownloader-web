from django.shortcuts import render
from django.http.request import HttpRequest
from django.http.response import HttpResponse

from sc.settings import STATIC_ROOT

from django.views.decorators.csrf import csrf_exempt

from sc.models import Track

import sc.lib as soundcloud

import json, os

def json_response(obj, *args, **kwargs):
    return HttpResponse(json.dumps(obj, indent=2), content_type='application/json', *args, **kwargs)

def index(request):
    return render(request, 'main/index.html')


def resolve(request):
    url = request.GET.get('url')
    key = request.GET.get('key')

    if url:
        response = soundcloud.resolve(url)
    else:
        response = {
            "error":"Must provide the GET parameter 'url'"
        }

    return json_response(response)

def static(request, path):
    content_type = "text/html"
    if ".css" in path:
        content_type = "text/css"
    filename = STATIC_ROOT + path
    text = open(filename, "rb").read()
    print("Serving staticfile: [%s]" % filename)
    response = HttpResponse(text, content_type=content_type)
    return response

def render_cards(request):
    url = request.GET.get('url')
    key = request.GET.get('key')

    if url:
        response = soundcloud.resolve(url)
    else:
        response = None
    context = {
        "json":json.dumps(response),
        "track":response
    }
    return render(request, 'components/cards.html', context)
