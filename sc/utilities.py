from multiprocessing import Process
from threading import Thread
from wsgiref.util import FileWrapper
from django.http import HttpResponse
import os
import sqlite3
from sc.settings import BASE_DIR
from sc.views import COMPLETE_DIR, INCOMPLETE_DIR
import json

def spawn_worker(task, *args, **kwargs):
    process = Process(target=task, args=args, kwargs=kwargs)
    process.start()
    return process

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


class ObjectCache:
    def __init__(self, name):
        self.name = name
        self.connection = sqlite3.connect(BASE_DIR + "/objects.db")
        try:
            self.connection.execute("SELECT 1 FROM %s" % name)
        except Exception as e:
            print(type(e))
            self.connection.execute("CREATE TABLE %s (K VARCHAR(16),V VARCHAR(20000), PRIMARY KEY(K) )" % self.name)

    def __getitem__(self, item):
        cursor = self.connection.execute("SELECT V FROM {} WHERE K=?".format(self.name), (item,)) # type: sqlite3.Cursor
        return json.loads(cursor.fetchone()[0])

    def __setitem__(self, key, value):
        self.connection.execute("INSERT OR REPLACE INTO {} (K,V) VALUES(?, ?)".format(self.name), (key, json.dumps(value)))

    def __contains__(self, item):
        res = self.connection.execute("SELECT 1 FROM {} WHERE K=?".format(self.name), (item,)).fetchone()
        return res is not None

    def __iter__(self):
        res = self.connection.execute("SELECT K FROM {}".format(self.name)).fetchall()
        for tup in res:
            yield tup[0]

