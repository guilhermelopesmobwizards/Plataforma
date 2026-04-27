from django.db import models
from .campaign import Campaign


class Comparison(models.Model):
    """
    Client-reported vs platform-reported comparison data (1-to-1 with Campaign).
    """

    campaign = models.OneToOneField(
        Campaign,
        on_delete=models.CASCADE,
        related_name="comparison",
        db_column="id_campaign",
    )

    client_conv = models.IntegerField(null=True, blank=True)
    client_rev = models.DecimalField(
        max_digits=14, decimal_places=4, null=True, blank=True
    )
    var_conv = models.DecimalField(
        max_digits=14, decimal_places=4, null=True, blank=True
    )
    var_rev = models.DecimalField(
        max_digits=14, decimal_places=4, null=True, blank=True
    )
    var_conv_pct = models.DecimalField(
        max_digits=10, decimal_places=6, null=True, blank=True
    )
    var_rev_pct = models.DecimalField(
        max_digits=10, decimal_places=6, null=True, blank=True
    )
    ok_conv = models.CharField(max_length=10, null=True, blank=True)
    ok_rev = models.CharField(max_length=10, null=True, blank=True)

    class Meta:
        db_table = "comparison"

    def __str__(self) -> str:
        return f"Comparison → Campaign #{self.campaign_id}"
