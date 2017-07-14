from django.shortcuts import render
from django.http.request import HttpRequest
from django.http.response import HttpResponse

from sc.settings import STATIC_ROOT
from sc.utilities import spawn_worker, hr_base10, send_file, duration_to_hms, hr_filesize
from time import sleep

from django.views.decorators.csrf import csrf_exempt

from sc.models import Track

import sc.lib as soundcloud



import json, os

DOWNLOAD_DIR = "/tmp/sc/"
INCOMPLETE_DIR = DOWNLOAD_DIR + "part/"
COMPLETE_DIR = DOWNLOAD_DIR + "done/"

for path in [DOWNLOAD_DIR, COMPLETE_DIR, INCOMPLETE_DIR]:
    if not os.path.exists(path):
        os.mkdir(path)

def fetch_track(track):
    filename = INCOMPLETE_DIR + "%s.mp3" % track['id']
    soundcloud.track_to_file(track, filename)
    os.rename(filename, COMPLETE_DIR + "%s.mp3" % track['id'])

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
    response = {"status":"downloading"}
    filename = COMPLETE_DIR + "%s.mp3" % id
    for t in range(20):
        if os.path.exists(filename):
            response['status'] = "ready"
            response['size'] = hr_filesize(os.path.getsize(filename))
            break
        sleep(0.5)
    return json_response(response)


workers = {}
def web_get_file(request, id, name):
    filename = COMPLETE_DIR + "%s.mp3" % id
    if os.path.exists(filename):
        return send_file(request, filename, name)
    return HttpResponse(status=404)

def render_cards(request):
    url = request.GET.get('url')
    key = request.GET.get('key')

    if url:
        response = soundcloud.resolve(url)
        if response['kind'] == "track":
            response['playback_count'] = hr_base10(response['playback_count'])
            response['likes_count'] = hr_base10(response['likes_count'])
            response['artwork_url'] = soundcloud.get_300px_album_art(response)
            response['filename'] = response['user']['username'] + " - " + response['title'] + ".mp3"
            response['duration'] = duration_to_hms(response['duration'])
            spawn_worker(fetch_track, response)
    else:
        response = None
    context = {
        "json":json.dumps(response),
        "track":response
    }
    return render(request, 'components/cards.html', context)
