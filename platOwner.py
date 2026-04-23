from django.db import models
from .campaign import Campaign


class Metric(models.Model):
    """
    Financial and performance metrics for a single campaign (1-to-1).
    Decimal precisions match the SQL schema exactly.
    """

    campaign = models.OneToOneField(
        Campaign,
        on_delete=models.CASCADE,
        related_name="metric",
        db_column="id_campaign",
    )

    cpa = models.DecimalField(max_digits=14, decimal_places=6, null=True, blank=True)
    er_cpa = models.DecimalField(max_digits=14, decimal_places=6, null=True, blank=True)
    er_cost = models.DecimalField(
        max_digits=14, decimal_places=6, null=True, blank=True
    )
    cost_ts = models.DecimalField(
        max_digits=14, decimal_places=4, null=True, blank=True
    )
    conv = models.IntegerField(null=True, blank=True)  # Conversions
    cost_eur = models.DecimalField(
        max_digits=14, decimal_places=4, null=True, blank=True
    )
    revenue_eur = models.DecimalField(
        max_digits=14, decimal_places=4, null=True, blank=True
    )
    margin_eur = models.DecimalField(
        max_digits=14, decimal_places=4, null=True, blank=True
    )
    roi = models.DecimalField(max_digits=14, decimal_places=6, null=True, blank=True)

    class Meta:
        db_table = "metric"

    def __str__(self) -> str:
        return f"Metric → Campaign #{self.campaign_id}"
