from decimal import Decimal

from django.core.paginator import Paginator
from django.db.models import Avg, Count, F, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render

from .excel_import import ExcelImportView  # noqa: F401
from core import models


def _safe(val):
    return float(val) if isinstance(val, Decimal) else val


def _base_ctx():
    return {
        "clients": models.Client.objects.only("id", "name", "code").order_by("name"),
        "platforms": models.Platform.objects.order_by("name"),
        "categories": models.Category.objects.order_by("name"),
        "countries": models.Country.objects.order_by("name"),
        "months": models.Month.objects.order_by("-month_date")[:24],
    }


def _filter_campaigns(get):
    qs = models.Campaign.objects.select_related(
        "month", "client", "country", "platform", "category"
    )
    for field, param in [
        ("client_id", "client"),
        ("platform_id", "platform"),
        ("category_id", "category"),
        ("country_id", "country"),
        ("month__month_date__year", "year"),
        ("month__month_date__month", "month"),
    ]:
        if v := get.get(param):
            qs = qs.filter(**{field: v})
    if (cc := get.get("client_camp")) is not None:
        qs = qs.filter(client_camp=(cc.lower() == "true"))
    return qs


def dashboard_view(request):
    return render(request, "endmonthapp/dashboard.html", _base_ctx())


def campaign_list_view(request):
    return render(request, "endmonthapp/campaigns.html", _base_ctx())


def metrics_view(request):
    return render(request, "endmonthapp/metrics.html", _base_ctx())


def comparisons_view(request):
    return render(request, "endmonthapp/comparisons.html", _base_ctx())


def clients_view(request):
    return render(request, "endmonthapp/clients.html", _base_ctx())


def workers_view(request):
    return render(request, "endmonthapp/worker.html", _base_ctx())


def platforms_view(request):
    return render(request, "endmonthapp/platforms.html", _base_ctx())


def configurations_view(request):
    return render(
        request,
        "endmonthapp/configurations.html",
        {
            **_base_ctx(),
            "creatives": models.Creative.objects.order_by("name"),
            "plat_owners": models.PlatOwner.objects.order_by("name"),
            "detail_types": models.DetailType.objects.order_by("name"),
        },
    )


def campaign_detail_view(request, pk):
    campaign = get_object_or_404(
        models.Campaign.objects.select_related(
            "month",
            "client",
            "country",
            "platform",
            "category",
            "creative",
            "plat_owner",
            "worker",
        ).prefetch_related("metric", "comparison"),
        pk=pk,
    )
    return render(
        request,
        "endmonthapp/campaign_detail.html",
        {"campaign": campaign, **_base_ctx()},
    )


def api_campaigns(request):
    qs = (
        _filter_campaigns(request.GET)
        .prefetch_related("metric", "comparison")
        .order_by("-month__month_date")
    )
    page = Paginator(qs, min(int(request.GET.get("page_size", 25)), 100)).get_page(
        request.GET.get("page", 1)
    )

    def _metric(c):
        m = getattr(c, "metric", None)
        if not m:
            return None
        return {
            "cpa": _safe(m.cpa),
            "er_cpa": _safe(m.er_cpa),
            "er_cost": _safe(m.er_cost),
            "cost_ts": _safe(m.cost_ts),
            "conv": m.conv,
            "cost_eur": _safe(m.cost_eur),
            "revenue_eur": _safe(m.revenue_eur),
            "margin_eur": _safe(m.margin_eur),
            "roi": _safe(m.roi),
        }

    def _comparison(c):
        cp = getattr(c, "comparison", None)
        if not cp:
            return None
        return {
            "client_conv": cp.client_conv,
            "client_rev": _safe(cp.client_rev),
            "var_conv": _safe(cp.var_conv),
            "var_rev": _safe(cp.var_rev),
            "var_conv_pct": _safe(cp.var_conv_pct),
            "var_rev_pct": _safe(cp.var_rev_pct),
            "ok_conv": cp.ok_conv,
            "ok_rev": cp.ok_rev,
        }

    return JsonResponse(
        {
            "count": page.paginator.count,
            "pages": page.paginator.num_pages,
            "page": page.number,
            "results": [
                {
                    "id": c.id,
                    "client": c.client.name or c.client.code,
                    "month": c.month.label or str(c.month.month_date),
                    "country": c.country.name,
                    "platform": c.platform.name if c.platform else None,
                    "category": c.category.name if c.category else None,
                    "client_camp": c.client_camp,
                    "invoice_google": c.invoice_google,
                    "metric": _metric(c),
                    "comparison": _comparison(c),
                }
                for c in page.object_list
            ],
        }
    )


def api_campaign_detail(request, pk):
    c = get_object_or_404(
        models.Campaign.objects.select_related(
            "month",
            "client",
            "country",
            "platform",
            "category",
            "creative",
            "plat_owner",
            "worker",
        ).prefetch_related("metric", "comparison"),
        pk=pk,
    )
    m = getattr(c, "metric", None)
    cp = getattr(c, "comparison", None)
    return JsonResponse(
        {
            "id": c.id,
            "month": c.month.label or str(c.month.month_date),
            "client": c.client.name,
            "country": c.country.name,
            "platform": c.platform.name if c.platform else None,
            "category": c.category.name if c.category else None,
            "creative": c.creative.name if c.creative else None,
            "plat_owner": c.plat_owner.name if c.plat_owner else None,
            "client_camp": c.client_camp,
            "invoice_google": c.invoice_google,
            "metric": (
                {
                    "cpa": _safe(m.cpa),
                    "er_cpa": _safe(m.er_cpa),
                    "er_cost": _safe(m.er_cost),
                    "cost_ts": _safe(m.cost_ts),
                    "conv": m.conv,
                    "cost_eur": _safe(m.cost_eur),
                    "revenue_eur": _safe(m.revenue_eur),
                    "margin_eur": _safe(m.margin_eur),
                    "roi": _safe(m.roi),
                }
                if m
                else None
            ),
            "comparison": (
                {
                    "client_conv": cp.client_conv,
                    "client_rev": _safe(cp.client_rev),
                    "var_conv": _safe(cp.var_conv),
                    "var_rev": _safe(cp.var_rev),
                    "var_conv_pct": _safe(cp.var_conv_pct),
                    "var_rev_pct": _safe(cp.var_rev_pct),
                    "ok_conv": cp.ok_conv,
                    "ok_rev": cp.ok_rev,
                }
                if cp
                else None
            ),
        }
    )


def api_dashboard(request):
    qs = _filter_campaigns(request.GET)

    def rows(q):
        return [{k: _safe(v) for k, v in r.items()} for r in q]

    return JsonResponse(
        {
            "totals": {
                k: _safe(v)
                for k, v in qs.aggregate(
                    total_campaigns=Count("id"),
                    total_revenue=Sum("metric__revenue_eur"),
                    total_cost=Sum("metric__cost_eur"),
                    total_margin=Sum("metric__margin_eur"),
                    total_conv=Sum("metric__conv"),
                    avg_roi=Avg("metric__roi"),
                    avg_cpa=Avg("metric__cpa"),
                ).items()
            },
            "by_platform": rows(
                qs.values(platform_name=F("platform__name"))
                .annotate(
                    campaigns=Count("id"),
                    revenue=Sum("metric__revenue_eur"),
                    cost=Sum("metric__cost_eur"),
                    conv=Sum("metric__conv"),
                )
                .order_by("-revenue")
            ),
            "by_month": rows(
                qs.values(month_date=F("month__month_date"), label=F("month__label"))
                .annotate(
                    campaigns=Count("id"),
                    revenue=Sum("metric__revenue_eur"),
                    cost=Sum("metric__cost_eur"),
                    conv=Sum("metric__conv"),
                )
                .order_by("month_date")
            ),
            "by_client": rows(
                qs.values(client_name=F("client__name"))
                .annotate(
                    campaigns=Count("id"),
                    revenue=Sum("metric__revenue_eur"),
                )
                .order_by("-revenue")[:10]
            ),
        }
    )


def api_metrics(request):
    qs = _filter_campaigns(request.GET)

    def rows(q):
        return [{k: _safe(v) for k, v in r.items()} for r in q]

    return JsonResponse(
        {
            "totals": {
                k: _safe(v)
                for k, v in qs.aggregate(
                    avg_cpa=Avg("metric__cpa"),
                    avg_roi=Avg("metric__roi"),
                    total_conv=Sum("metric__conv"),
                ).items()
            },
            "by_platform": rows(
                qs.values(platform_name=F("platform__name"))
                .annotate(avg_cpa=Avg("metric__cpa"), conv=Sum("metric__conv"))
                .order_by("-conv")
            ),
            "by_client": rows(
                qs.values(client_name=F("client__name"))
                .annotate(avg_roi=Avg("metric__roi"), campaigns=Count("id"))
                .order_by("-avg_roi")[:10]
            ),
            "by_month": rows(
                qs.values(month_date=F("month__month_date"), label=F("month__label"))
                .annotate(conv=Sum("metric__conv"))
                .order_by("month_date")
            ),
        }
    )


def api_comparisons(request):
    qs = _filter_campaigns(request.GET)

    def rows(q):
        return [{k: _safe(v) for k, v in r.items()} for r in q]

    return JsonResponse(
        {
            "by_month": rows(
                qs.values(month_date=F("month__month_date"), label=F("month__label"))
                .annotate(
                    revenue=Sum("metric__revenue_eur"),
                    cost=Sum("metric__cost_eur"),
                    conv=Sum("metric__conv"),
                    avg_roi=Avg("metric__roi"),
                )
                .order_by("month_date")
            ),
            "by_client": rows(
                qs.values(
                    client_name=F("client__name"),
                    month_date=F("month__month_date"),
                    label=F("month__label"),
                )
                .annotate(
                    revenue=Sum("metric__revenue_eur"),
                    conv=Sum("metric__conv"),
                    avg_roi=Avg("metric__roi"),
                    avg_cpa=Avg("metric__cpa"),
                )
                .order_by("client_name", "month_date")
            ),
            "by_platform": rows(
                qs.values(
                    platform_name=F("platform__name"),
                    month_date=F("month__month_date"),
                    label=F("month__label"),
                )
                .annotate(
                    cost=Sum("metric__cost_eur"),
                    revenue=Sum("metric__revenue_eur"),
                    avg_roi=Avg("metric__roi"),
                )
                .order_by("platform_name", "month_date")
            ),
        }
    )
