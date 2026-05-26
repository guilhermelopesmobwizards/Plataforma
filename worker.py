from django.db import models
from django.contrib.auth import get_user_model
from simple_history.models import HistoricalRecords
from .base import TimestampedModel
from .campaign import Campaign

User = get_user_model()

MODES = [("override", "Override"), ("addition", "Addition")]


class ConversionAdjustment(TimestampedModel):
    campaign = models.ForeignKey(
        Campaign,
        on_delete=models.CASCADE,
        related_name="adjustments",
    )
    operator = models.CharField(max_length=200)
    count = models.IntegerField()
    payout = models.DecimalField(max_digits=14, decimal_places=4)
    payout_currency = models.CharField(max_length=10)
    mode = models.CharField(max_length=10, choices=MODES, default="addition")
    created_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="conversion_adjustments",
    )
    history = HistoricalRecords()

    class Meta:
        db_table = "conversion_adjustment"
        unique_together = [("campaign", "operator")]

    def __str__(self):
        return f"Adjustment #{self.pk} — {self.campaign} / {self.operator}"
