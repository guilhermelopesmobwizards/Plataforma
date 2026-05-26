from django.db import models
from .base import TimestampedModel
from .country import Country


class Client(TimestampedModel):
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=120, null=True, blank=True, unique=True)
    base_country = models.ForeignKey(
        Country,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="clients",
        db_column="id_base_country",
    )

    class Meta:
        db_table = "client"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name or self.code
