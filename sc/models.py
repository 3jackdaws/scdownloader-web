from django.db.models import Model
from django.db import models

import json

SOUNDCLOUD_RESOURCE_TYPE = (
    (0, "Track"),
    (1, "Playlist"),
)


class DownloadLog(Model):
    type = models.IntegerField(choices=SOUNDCLOUD_RESOURCE_TYPE)
    resource_id = models.BigIntegerField()
    file = models.FileField(null=True)
    ip = models.GenericIPAddressField()


class Track(Model):
    id = models.BigIntegerField(primary_key=True)
    json = models.CharField(max_length=10000)
    retrieved_at = models.DateTimeField(auto_now=True)

    def get_track(self):
        return json.loads(self.json)