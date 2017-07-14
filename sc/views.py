from django.shortcuts import render
from django.http.request import HttpRequest
from django.http.response import HttpResponse

from sc.settings import STATIC_ROOT
from sc.utilities import spawn_worker, hr_base10, send_file, duration_to_hms
from time import sleep

from django.views.decorators.csrf import csrf_exempt

from sc.models import Track

import sc.lib as soundcloud



import json, os

DOWNLOAD_DIR = "/tmp/sc/"
if not os.path.exists(DOWNLOAD_DIR):
    os.mkdir(DOWNLOAD_DIR)

def json_response(obj, *args, **kwargs):
    return HttpResponse(json.dumps(obj, indent=2), content_type='application/json', *args, **kwargs)

def index(request):
    return render(request, 'main/index.html')


# def resolve(request):
#     url = request.GET.get('url')
#     key = request.GET.get('key')
#
#     if url:
#         response = soundcloud.resolve(url)
#         print(response['kind'])
#         if response['kind'] == "track":
#             print("preloading")
#             filename = DOWNLOAD_DIR + response['id'] + ".mp3"
#             workers[response['id']] = spawn_worker(soundcloud.track_to_file, track_obj=response, filename=filename)
#         else:
#             print("Not a track")
#     else:
#         response = {
#             "error":"Must provide the GET parameter 'url'"
#         }
#
#     return json_response(response)

def static(request, path):
    content_type = "text/html"
    if ".css" in path:
        content_type = "text/css"
    filename = STATIC_ROOT + path
    text = open(filename, "rb").read()
    print("Serving staticfile: [%s]" % filename)
    response = HttpResponse(text, content_type=content_type)
    return response

def track_status(request, id):
    response = {"ready":False}
    filename = DOWNLOAD_DIR + str(id) + ".mp3"
    for t in range(20):
        if id in filecache and filecache[id]['ready']:
            response['ready'] = True
            break
        sleep(0.5)
    return json_response(response)


workers = {}
filecache = {}
def get_track(request, id, name):
    response = {"url":None}
    if id in filecache and filecache[id]['ready']:
        filename = DOWNLOAD_DIR + str(id) + ".mp3"

            if os.path.exists(filename):
                return send_file(request, filename, name)
            sleep(1)
    else:
        filename = DOWNLOAD_DIR + str(id) + ".mp3"
        workers[int(id)] = spawn_worker(soundcloud.track_to_file, track_obj=response, filename=filename)
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

            filename = DOWNLOAD_DIR + str(response['id']) + ".mp3"
            workers[response['id']] = spawn_worker(soundcloud.track_to_file, track_obj=response, filename=filename)
    else:
        response = None
    context = {
        "json":json.dumps(response),
        "track":response
    }
    return render(request, 'components/cards.html', context)
