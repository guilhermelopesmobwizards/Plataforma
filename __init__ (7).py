from django.db import models
from .base import TimestampedModel


class ExchangeRate(TimestampedModel):
    """
    Monthly exchange rate relative to EUR.
    One row per currency per month.
    """

    month = models.PositiveSmallIntegerField()  # 1–12
    year = models.PositiveSmallIntegerField()  # ex: 2026
    currency = models.CharField(max_length=3)  # ISO 4217 ex: USD, GBP, AED
    rate = models.DecimalField(max_digits=18, decimal_places=6)  # 1 EUR = X currency
    is_locked = models.BooleanField(default=False)  # manual override — skipped by auto-compute

    class Meta:
        db_table = "exchange_rate"
        constraints = [
            models.UniqueConstraint(
                fields=["year", "month", "currency"],
                name="exchange_rate_unique_period_currency",
            )
        ]
        ordering = ["-year", "-month", "currency"]

    def __str__(self) -> str:
        return f"{self.currency} {self.year}-{self.month:02d}: {self.rate}"
