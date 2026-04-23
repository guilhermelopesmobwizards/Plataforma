from django.db import models


class DetailType(models.Model):
    name = models.CharField(max_length=40, unique=True)

    class Meta:
        db_table = "detail_type"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name
