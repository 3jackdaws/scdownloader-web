from sc.lib import resolve

def func(**kwargs):
    for key in kwargs:
        print(key, kwargs[key])



dictionary = {
    "one":1,
    "two":2
}


class itemdict(dict):
    def __getattr__(self, item):
        return self.__getitem__(item)




thing = itemdict(four=4, two=2)

class Track:
    def __init__(self, track:dict):
        self.internal = {}
        self.__dict__.update(track)

    def __getitem__(self, item):
        return self.internal[item]

    def __setitem__(self, key, value):
        self.internal[key] = value

    def __str__(self):
        return self.title


t = resolve("https://soundcloud.com/trshlrd/moonlit?in=ian-murphy-3jackdaws/sets/gud-music")

track = Track(t)

track.__getattribute__(var)
