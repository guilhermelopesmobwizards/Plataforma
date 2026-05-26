from django.db import models
from .base import TimestampedModel


class Category(TimestampedModel):
    name = models.CharField(max_length=80, unique=True)

    class Meta:
        db_table = "category"
        verbose_name_plural = "categories"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name
