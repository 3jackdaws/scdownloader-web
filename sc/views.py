from django.shortcuts import render
from django.http.request import HttpRequest
from django.http.response import HttpResponse

from sc.settings import STATIC_ROOT
from sc.utilities import *
from time import sleep

from django.views.decorators.csrf import csrf_exempt

import sc.lib as soundcloud

from redis import Redis

import json, os


def json_response(obj, *args, **kwargs):
    return HttpResponse(json.dumps(obj, indent=2), content_type='application/json', *args, **kwargs)

def index(request):
    return render(request, 'main/index.html')


def static(request, path):
    content_type = "text/html"
    if ".css" in path:
        content_type = "text/css"
    filename = STATIC_ROOT + path
    text = open(filename, "rb").read()
    print("Serving staticfile: [%s]" % filename)
    response = HttpResponse(text, content_type=content_type)
    return response


def api_track_status(request, id):
    track = Track(id)
    response = {}

    if track.status == "DOWNLOADING":
        for i in range(20):
            sleep(0.5)
            if track.ready:
                break

    if track.ready:
        filename = track.path
        response['status'] = track.status
        response['size'] = hr_filesize(os.path.getsize(filename))
    else:
        response['status'] = track.status
    return json_response(response)


def web_get_file(request, id, name):
    filename = Track(id).path
    if filename is not None:
        return send_file(request, filename, name)
    return HttpResponse(status=404)


def render_cards(request):
    url = request.GET.get('url')
    key = request.GET.get('key')

    if url:
        track = Track.from_url(url)
        if track['kind'] == "track":
            response = track.formatted
            track.signal_download()
    else:
        response = None
    context = {
        "json":json.dumps(response),
        "track":response
    }
    return render(request, 'components/cards.html', context)
