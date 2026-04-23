from django.contrib import admin

# Register your models here.
"""
endmonthapp/admin.py

Django Admin configuration for all MAP Control models.
Metric and Comparison are registered as Campaign inlines.
"""
from .models import (
    Month,
    Country,
    Client,
    Category,
    Creative,
    Platform,
    PlatOwner,
    Team,
    DetailType,
    Campaign,
    Metric,
    Comparison,
)


class MetricInline(admin.StackedInline):
    model = Metric
    extra = 1
    can_delete = False


class ComparisonInline(admin.StackedInline):
    model = Comparison
    extra = 1
    can_delete = False


@admin.register(Month)
class MonthAdmin(admin.ModelAdmin):
    list_display = ("month_date", "year", "month_num", "label")
    search_fields = ("label",)
    ordering = ("-month_date",)


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ("iso_code", "name")
    search_fields = ("iso_code", "name")


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "base_country")
    search_fields = ("code", "name")
    list_select_related = ("base_country",)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Creative)
class CreativeAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Platform)
class PlatformAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(PlatOwner)
class PlatOwnerAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ("ts_manager", "ts_head", "client_manager", "pm")
    search_fields = ("ts_manager", "ts_head", "pm")


@admin.register(DetailType)
class DetailTypeAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = (
        "id",
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
        "client__name",
        "client__code",
        "invoice_google",
        "country__name",
    )
    list_select_related = ("client", "month", "country", "platform", "category")
    inlines = [MetricInline, ComparisonInline]
    autocomplete_fields = [
        "client",
        "country",
        "platform",
        "category",
        "creative",
        "team",
        "plat_owner",
        "detail_type",
    ]


@admin.register(Metric)
class MetricAdmin(admin.ModelAdmin):
    list_display = ("campaign", "cost_eur", "revenue_eur", "margin_eur", "roi", "conv")
    list_select_related = ("campaign",)


@admin.register(Comparison)
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
