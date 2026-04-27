from django.db import models


class PlatOwner(models.Model):
    name = models.CharField(max_length=60, unique=True)

    class Meta:
        db_table = "plat_owner"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name
