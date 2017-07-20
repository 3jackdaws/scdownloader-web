from multiprocessing import Process
from threading import Thread
from wsgiref.util import FileWrapper
from django.http import HttpResponse
import os
import sqlite3
from sc.settings import BASE_DIR, REDIS_HOST
import json
from sc.lib import track_to_file, track_from
import redis
from sc.lib import get_300px_album_art, resolve

EXPIRE_TIME = 3600
DOWNLOAD_DIR = "/tmp/sc/"
COMPLETE_DIR = DOWNLOAD_DIR + "done/"
INCOMPLETE_DIR = DOWNLOAD_DIR + "part/"

for path in [DOWNLOAD_DIR, INCOMPLETE_DIR, COMPLETE_DIR]:
    if not os.path.exists(path):
        os.mkdir(path)

def hr_base10(num, suffix=''):
    if num-1000 <= 0:
        return str(num)
    for unit in ['','K','M','B','T']:
        if abs(num) < 1000.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1000.0
    return "%.1f%s%s" % (num, 'Yi', suffix)

def hr_filesize(num, suffix='B'):
    for unit in ['','K','M','G','T']:
        if abs(num) < 1000.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)

def send_file(request, filename, name):
    """
    Send a file through Django without loading the whole file into
    memory at once. The FileWrapper will turn the file object into an
    iterator for chunks of 8KB.
    """
    wrapper = FileWrapper(open(filename, "rb"))
    response = HttpResponse(wrapper, content_type='X-DOWNLOAD')
    response['Content-Length'] = os.path.getsize(filename)
    response['Content-Disposition'] = 'attachment; filename=%s' % name
    return response


def duration_to_hms(duration):
    seconds = duration/1000
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return "%02d:%02d" % (m, s)


def track_downloading(id):
    return os.path.exists(INCOMPLETE_DIR + "%s.mp3" % id)


def track_exists(id):
    return os.path.exists(COMPLETE_DIR + "%s.mp3" % id)


def track_path(id):
    return COMPLETE_DIR + "%s.mp3" % id


def fetch_track(track):
    filename = INCOMPLETE_DIR + "%s.mp3" % track['id']
    track_to_file(track, filename)
    new_path = COMPLETE_DIR + "%s.mp3" % track['id']
    os.rename(filename, new_path)


def cached_track(id, redis_connection:redis.Redis):

    track_obj_key = "TRACK-%s" % id
    track_status_key = "STATUS-%s" % id
    try:
        track = json.loads(redis_connection.get(track_obj_key).decode('utf-8'))
        redis_connection.expire(track_obj_key, EXPIRE_TIME)
        redis_connection.expire(track_status_key, EXPIRE_TIME)
    except:
        track = track_from(id)
        redis_connection.setex(track_obj_key, json.dumps(track), EXPIRE_TIME)
        redis_connection.expire(track_status_key, EXPIRE_TIME)
    return track

cache = redis.Redis(REDIS_HOST)




class Track:
    def __init__(self, id):
        self.id = int(id)
        self.was_cached = True
        self.track = self._fetch()

    def __getitem__(self, item):
        return self.track[item]

    def __str__(self):
        return "%s - %s" % (self.track['user']['username'], self.track['title'])

    def __repr__(self):
        return "<Track(%s)>" % self.id

    def _fetch(self):
        track = None
        try:
            track = json.loads(cache.get("TRK(%s).OBJ" % self.id))
        except Exception as e:
            self.was_cached = False
            track = track_from(self.id)
            cache.setex("TRK(%s).OBJ" % self.id, json.dumps(track), EXPIRE_TIME)

        return track

    
    @property
    def formatted(self):
        track = self.track
        track['playback_count'] = hr_base10(track['playback_count'])
        track['likes_count'] = hr_base10(track['likes_count'])
        track['artwork_url'] = get_300px_album_art(track)
        track['filename'] = track['user']['username'] + " - " + track['title'] + ".mp3"
        track['duration'] = duration_to_hms(track['duration'])
        return track
    
    @property
    def ready(self):
        return self.status == "READY"

    @property
    def status(self):
        stat = cache.get("TRK(%s).STAT" % self.id)
        return stat.decode('utf-8') if stat else "NOT CACHED"

    @status.setter
    def status(self, value):
        cache.setex("TRK(%s).STAT" % self.id, value, EXPIRE_TIME)

    @property
    def path(self):
        path = COMPLETE_DIR + "%s.mp3" % self.id
        return path if os.path.exists(path) else None

    def prepare(self):
        incomplete_path = INCOMPLETE_DIR + "%s.mp3" % self.id
        complete_path = COMPLETE_DIR + "%s.mp3" % self.id
        if not os.path.exists(complete_path):
            self.status = "DOWNLOADING"
            track_to_file(self.track, incomplete_path)
            os.rename(incomplete_path, complete_path)
            self.status = "READY"
        return complete_path

    def signal_download(self):
        cache.publish("DOWNLOAD-QUEUE", self.id)

    @staticmethod
    def from_url(url):
        track = resolve(url)
        cache.setex("TRK(%s).OBJ" % track['id'], json.dumps(track), EXPIRE_TIME)
        return Track(track['id'])

def track_downloader():
    listener = cache.pubsub()
    listener.subscribe("DOWNLOAD-QUEUE")
    for message in listener.listen():
        if message['type'] == "message":
            track_id = message['data'].decode('utf-8')
            track = Track(track_id)
            track.prepare()
            track.status = "READY"

downloader = Process(target=track_downloader)
downloader.start()