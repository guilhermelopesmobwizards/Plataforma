from django.db import models
from .base import TimestampedModel


class DailyExchangeRate(TimestampedModel):
    """
    One row per calendar day per currency.
    Rate is 1 EUR = X currency, sourced from exchangerate-api.com.
    Monthly averages are computed from these rows into ExchangeRate.
    """

    date = models.DateField()
    currency = models.CharField(max_length=3)
    rate = models.DecimalField(max_digits=18, decimal_places=6)

    class Meta:
        db_table = "daily_exchange_rate"
        constraints = [
            models.UniqueConstraint(
                fields=["date", "currency"],
                name="daily_exchange_rate_unique_date_currency",
            )
        ]
        ordering = ["-date", "currency"]
        indexes = [
            models.Index(fields=["date"], name="daily_exrate_date_idx"),
            models.Index(fields=["currency"], name="daily_exrate_currency_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.currency} {self.date}: {self.rate}"
