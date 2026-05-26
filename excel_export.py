from django.contrib import admin
from . import models

# Register your models here.
"""
endmonthapp/admin.py

Django Admin configuration for all MAP Control models.
Metric and Comparison are registered as Campaign inlines.
"""


class MetricInline(admin.StackedInline):
    model = models.Metric
    extra = 1
    can_delete = False


class ComparisonInline(admin.StackedInline):
    model = models.Comparison
    extra = 1
    can_delete = False


class ConversionInline(admin.TabularInline):
    model = models.Conversion
    extra = 0
    can_delete = False
    readonly_fields = ("operator", "event", "count", "revenue", "payout", "payout_currency", "payout_start_date", "payout_end_date", "math")


@admin.register(models.Month)
class MonthAdmin(admin.ModelAdmin):
    list_display = ("month_date", "year", "month_num", "label")
    search_fields = ("label",)
    ordering = ("-month_date",)


@admin.register(models.Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ("iso_code", "name")
    search_fields = ("iso_code", "name")


@admin.register(models.Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "base_country")
    search_fields = ("code", "name")
    list_select_related = ("base_country",)


@admin.register(models.Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(models.Creative)
class CreativeAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(models.Platform)
class PlatformAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(models.PlatOwner)
class PlatOwnerAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(models.Worker)
class WorkerAdmin(admin.ModelAdmin):
    list_display = ("ts_manager", "ts_head", "client_manager", "pm")
    search_fields = ("ts_manager", "ts_head", "pm")


@admin.register(models.DetailType)
class DetailTypeAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(models.Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "campaign_id",
        "client",
        "month",
        "country",
        "platform",
        "category",
        "client_camp",
        "invoice_google",
    )
    list_filter = ("platform", "category", "client_camp", "month__month_date")
    search_fields = (
        "campaign_id",
        "client__name",
        "client__code",
        "invoice_google",
        "country__name",
    )
    list_select_related = ("client", "month", "country", "platform", "category")
    inlines = [MetricInline, ComparisonInline, ConversionInline]
    autocomplete_fields = [
        "client",
        "country",
        "platform",
        "category",
        "creative",
        "worker",
        "plat_owner",
        "detail_type",
    ]


@admin.register(models.Metric)
class MetricAdmin(admin.ModelAdmin):
    list_display = ("campaign", "cost_eur", "revenue_eur", "margin_eur", "roi", "conv")
    list_select_related = ("campaign",)


@admin.register(models.Comparison)
class ComparisonAdmin(admin.ModelAdmin):
    list_display = (
        "campaign",
        "client_conv",
        "client_rev",
        "var_conv_pct",
        "var_rev_pct",
        "ok_conv",
        "ok_rev",
    )
    list_select_related = ("campaign",)


@admin.register(models.ExchangeRate)
class ExchangeRateAdmin(admin.ModelAdmin):
    list_display = ("currency", "year", "month", "rate", "is_locked", "updated_at")
    list_filter = ("currency", "year", "is_locked")
    ordering = ("-year", "-month", "currency")
    readonly_fields = ("created_at", "updated_at")


@admin.register(models.DailyExchangeRate)
class DailyExchangeRateAdmin(admin.ModelAdmin):
    list_display = ("date", "currency", "rate", "updated_at")
    list_filter = ("currency",)
    date_hierarchy = "date"
    ordering = ("-date", "currency")
    readonly_fields = ("date", "currency", "rate", "created_at", "updated_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
