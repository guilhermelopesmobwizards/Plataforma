"""
endmonthapp/models.py

Django ORM models mirroring the MAP Control SQL schema exactly.
Lookup tables first, then the Campaign fact table, then Metric and Comparison.
"""

from django.db import models


class Month(models.Model):
    """
    Stores one row per calendar month.
    'year' and 'month_num' are read-only properties that mirror the
    GENERATED columns in MySQL — computed on the fly, not stored separately.
    """

    month_date = models.DateField(unique=True)
    label = models.CharField(max_length=20, null=True, blank=True)

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


class Country(models.Model):
    iso_code = models.CharField(max_length=3, unique=True)
    name = models.CharField(max_length=80, null=True, blank=True)

    class Meta:
        db_table = "country"
        verbose_name_plural = "countries"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name or self.iso_code


class Client(models.Model):
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=120, null=True, blank=True)
    base_country = models.ForeignKey(
        Country,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="clients",
        db_column="id_base_country",
    )

    class Meta:
        db_table = "client"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name or self.code


class Category(models.Model):
    name = models.CharField(max_length=80, unique=True)

    class Meta:
        db_table = "category"
        verbose_name_plural = "categories"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Creative(models.Model):
    name = models.CharField(max_length=80, unique=True)

    class Meta:
        db_table = "creative"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Platform(models.Model):
    name = models.CharField(max_length=60, unique=True)

    class Meta:
        db_table = "platform"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class PlatOwner(models.Model):
    name = models.CharField(max_length=60, unique=True)

    class Meta:
        db_table = "plat_owner"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Team(models.Model):

    ts_manager = models.CharField(max_length=20, null=True, blank=True)
    ts_head = models.CharField(max_length=20, null=True, blank=True)
    client_manager = models.CharField(max_length=20, null=True, blank=True)
    client_head = models.CharField(max_length=20, null=True, blank=True)
    fe = models.CharField(max_length=20, null=True, blank=True)  # Front-end
    be = models.CharField(max_length=20, null=True, blank=True)  # Back-end
    creative = models.CharField(max_length=20, null=True, blank=True)
    qa = models.CharField(max_length=20, null=True, blank=True)
    pm = models.CharField(max_length=20, null=True, blank=True)  # Project Manager

    class Meta:
        db_table = "team"
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "ts_manager",
                    "ts_head",
                    "client_manager",
                    "client_head",
                    "fe",
                    "be",
                    "creative",
                    "qa",
                    "pm",
                ],
                name="team_unique_combination",
            )
        ]

    def __str__(self) -> str:
        parts = [p for p in [self.ts_manager, self.ts_head, self.pm] if p]
        return " | ".join(parts) or f"Team #{self.pk}"


class DetailType(models.Model):
    name = models.CharField(max_length=40, unique=True)

    class Meta:
        db_table = "detail_type"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


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
