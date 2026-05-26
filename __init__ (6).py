from django.db import models
from .base import TimestampedModel


class DetailType(TimestampedModel):
    name = models.CharField(max_length=40, unique=True)

    class Meta:
        db_table = "detail_type"

    def __str__(self) -> str:
        return self.name
