from django.db import models
from .base import TimestampedModel


class Creative(TimestampedModel):
    name = models.CharField(max_length=80, unique=True)

    class Meta:
        db_table = "creative"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name
