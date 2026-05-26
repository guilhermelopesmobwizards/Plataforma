from django.db import models
from .base import TimestampedModel
from .campaign import Campaign


class Conversion(TimestampedModel):
    campaign = models.ForeignKey(
        Campaign,
        on_delete=models.CASCADE,
        related_name="conversions",
        db_column="id_campaign",
    )
    operator = models.CharField(max_length=200, blank=True, default="")
    event = models.CharField(max_length=200, blank=True, default="")
    count = models.IntegerField(default=0)
    revenue = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)
    payout = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)
    payout_currency = models.CharField(max_length=10, null=True, blank=True)
    payout_start_date = models.DateField(null=True, blank=True)
    payout_end_date = models.DateField(null=True, blank=True)
    math = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "conversion"
        constraints = [
            models.UniqueConstraint(
                fields=["campaign", "operator", "event", "payout_start_date"],
                name="conversion_unique_row",
            )
        ]

    def __str__(self) -> str:
        return f"Conversion → Campaign #{self.campaign_id} | {self.operator}/{self.event}"
