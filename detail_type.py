from django.db import models


class TimestampedModel(models.Model):
    """
    Abstract base that adds created_at and updated_at to every model that inherits it.
    Provides a full audit trail of when records were created and last modified.
    """

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
