from django.db import models


class Platform(models.Model):
    name = models.CharField(max_length=60, unique=True)

    class Meta:
        db_table = "platform"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name
