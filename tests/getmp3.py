from tests.common import json_response_to_dict, urlencode, get_html, urlopen, quote
import bs4
import mutagen
import sc.lib as soundcloud
import os, json


TEST_TRACKS = [
    "https://soundcloud.com/luxnatura/bamboo",
]


RESOLVE_URL = "http://localhost/get-cards?%s"
TEMP_FILE = "/tmp/temporary_test_file.mp3"


def check_equivalent(track_url):
    response = get_html(RESOLVE_URL % urlencode({"url":track_url}))
    soup = bs4.BeautifulSoup(response, 'html.parser')
    download_url = soup.find(id='download-button')['href']
    assert download_url is not None
    download_url = "http://localhost" + quote(download_url)
    fp = urlopen(download_url)
    mp3 = open(TEMP_FILE, "wb")
    track = soundcloud.resolve(track_url)
    mp3.write(fp.read())
    audio = mutagen.File(TEMP_FILE)
    assert audio.tags['TIT2'] == track['title']
    assert audio.tags['TPE1'] == track['user']['username']
    album_artwork = urlopen(soundcloud.get_300px_album_art(track)).read()
    assert album_artwork == audio.tags["APIC:Cover"].data
    os.remove(TEMP_FILE)
    print(track)

for url in TEST_TRACKS:
    try:
        check_equivalent(url)
        print("PASS", url)
    except:
        print("FAIL", url)




