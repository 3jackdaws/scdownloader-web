from sc.utilities import ObjectCache

cache = ObjectCache("test")
cache['test'] = 5
cache['test2'] = 3
# print(cache['test'])

for x in cache:
    print(x)