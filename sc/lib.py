from urllib.request import Request, urlopen
import json
import mutagen
import os


CLIENT_ID = "2t9loNQH90kzJcsFCODdigxfp325aq4z"

DOWNLOAD_DIR = "./"
if not os.path.exists(DOWNLOAD_DIR):
    os.mkdir(DOWNLOAD_DIR)

def get_url(url):
    try:
        return json.loads(urlopen(url).read().decode('utf-8'))
    except Exception as e:
        return {"error":str(e)}


def get_http_stream_url(track_id):
    url = "https://api.soundcloud.com/i1/tracks/%s/streams?client_id=%s" % (str(track_id), CLIENT_ID)
    try:
        return get_url(url)['http_mp3_128_url']
    except Exception as e:
        print(e)
        return None


def resolve(url):
    resolve_url = "https://api-v2.soundcloud.com/resolve?url=%s&client_id=%s&app_version=1499347238" % (url, CLIENT_ID)
    return get_url(resolve_url)

def get_stream_resource_from(url):
    track = resolve(url)
    stream_url = get_http_stream_url(track['id'])
    return urlopen(stream_url)

def get_300px_album_art(track_object):
    art_url = track_object['artwork_url']  # type: str
    return art_url.replace('large', 't300x300') if art_url else None

def embed_artwork(audio:mutagen.File, artwork_url):
    if artwork_url:
        audio.tags.add(
            mutagen.id3.APIC(
                encoding=3,
                mime='image/jpeg',
                type=3,
                desc=u'Cover',
                data=urlopen(artwork_url).read()
            )
        )
    return audio

def set_artist_title(audio:mutagen.File, artist, title):
    frame = mutagen.id3.TIT2(encoding=3)
    frame.append(title)
    audio.tags.add(frame)
    frame = mutagen.id3.TPE1(encoding=3)
    frame.append(artist)
    audio.tags.add(frame)
    return audio


def get_track_artist(track_obj):
    return track_obj['user']['username']


def track_to_file(track_obj, filename):
    print("Downloading %s" % filename)
    title = track_obj['title']
    artist = get_track_artist(track_obj)
    file = open(filename, "wb+")
    stream_url = get_http_stream_url(track_obj['id'])
    stream = urlopen(stream_url)
    file.write(stream.read())
    file.close()

    audio = mutagen.File(filename)
    audio.add_tags()

    audio = set_artist_title(audio, artist, title)
    audio = embed_artwork(audio, get_300px_album_art(track_obj))
    audio.save(filename, v1=2)

    return filename
