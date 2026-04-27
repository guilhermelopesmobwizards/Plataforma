from django.db import models


class Country(models.Model):
    iso_code = models.CharField(max_length=3, unique=True)
    name = models.CharField(max_length=80, null=True, blank=True)

    class Meta:
        db_table = "country"
        verbose_name_plural = "countries"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name or self.iso_code
