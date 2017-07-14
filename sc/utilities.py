from multiprocessing import Process
from threading import Thread
from wsgiref.util import FileWrapper
from django.http import HttpResponse
import os

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