from django.db import models
from .base import TimestampedModel


class PlatOwner(TimestampedModel):
    name = models.CharField(max_length=60, unique=True)

    class Meta:
        db_table = "plat_owner"

    def __str__(self) -> str:
        return self.name
