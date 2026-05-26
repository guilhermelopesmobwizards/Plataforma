from django.db import models
from simple_history.models import HistoricalRecords
from .base import TimestampedModel


class Month(TimestampedModel):
    """
    Stores one row per calendar month.
    'year' and 'month_num' are read-only properties that mirror the
    GENERATED columns in MySQL — computed on the fly, not stored separately.
    """

    month_date = models.DateField(unique=True)
    label = models.CharField(max_length=20, null=True, blank=True)
    is_closed = models.BooleanField(default=False)
    history = HistoricalRecords()

    class Meta:
        db_table = "month"
        ordering = ["month_date"]

    @property
    def year(self) -> int:
        return self.month_date.year

    @property
    def month_num(self) -> int:
        return self.month_date.month

    def __str__(self) -> str:
        return self.label or str(self.month_date)
