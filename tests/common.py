from urllib.request import urlopen
from urllib.parse import urlencode, quote
import json

def json_response_to_dict(url):
    return json.loads(urlopen(url).read().decode('utf-8'))


def get_html(url):
    return urlopen(url).read().decode('utf-8')