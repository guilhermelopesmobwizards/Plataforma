from django.db import models
from .month import Month
from .client import Client
from .country import Country
from .category import Category
from .creative import Creative
from .platform import Platform
from .platOwner import PlatOwner
from .team import Team
from .detailType import DetailType


class Campaign(models.Model):
    """
    Central fact table linking all dimension tables.
    month and client are required; all other FKs are optional.
    """

    month = models.ForeignKey(
        Month, on_delete=models.PROTECT, related_name="campaigns", db_column="id_month"
    )
    client = models.ForeignKey(
        Client,
        on_delete=models.PROTECT,
        related_name="campaigns",
        db_column="id_client",
    )
    country = models.ForeignKey(
        Country,
        on_delete=models.PROTECT,
        related_name="campaigns",
        db_column="id_country",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="campaigns",
        db_column="id_category",
    )
    creative = models.ForeignKey(
        Creative,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="campaigns",
        db_column="id_creative",
    )
    platform = models.ForeignKey(
        Platform,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="campaigns",
        db_column="id_platform",
    )
    plat_owner = models.ForeignKey(
        PlatOwner,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="campaigns",
        db_column="id_plat_owner",
    )
    team = models.ForeignKey(
        Team,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="campaigns",
        db_column="id_team",
    )
    detail_type = models.ForeignKey(
        DetailType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="campaigns",
        db_column="id_detail",
    )

    client_camp = models.BooleanField(null=True, blank=True)
    invoice_google = models.CharField(max_length=20, null=True, blank=True)

    class Meta:
        db_table = "campaign"
        ordering = ["-month__month_date"]
        indexes = [
            models.Index(fields=["month"], name="campaign_id_month_index"),
            models.Index(fields=["client"], name="campaign_id_client_index"),
            models.Index(fields=["country"], name="campaign_id_country_index"),
            models.Index(fields=["category"], name="campaign_id_category_index"),
            models.Index(fields=["creative"], name="campaign_id_creative_index"),
            models.Index(fields=["team"], name="campaign_id_team_index"),
        ]

    def __str__(self) -> str:
        return f"Campaign #{self.pk} — {self.client} / {self.month}"
