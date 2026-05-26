import logging
from datetime import date, timedelta

from celery import shared_task
from django.db import transaction

from core.services.cost_services import CostsService
from core import models

logger = logging.getLogger(__name__)


def _get_or_create_month(year: int, month: int):
    month_date = date(year, month, 1)
    obj, _ = models.Month.objects.get_or_create(
        month_date=month_date,
        defaults={"label": month_date.strftime("%b %Y")},
    )
    return obj


def _get_or_create_client(name: str):
    if not name:
        return None
    obj, _ = models.Client.objects.get_or_create(
        name=name,
        defaults={"code": name[:10].upper().replace(" ", "_")},
    )
    return obj


def _get_or_create_country(iso_code: str):
    if not iso_code:
        return None
    obj, _ = models.Country.objects.get_or_create(iso_code=iso_code)
    return obj


def _get_or_create_simple(model_class, name: str):
    if not name:
        return None
    obj, _ = model_class.objects.get_or_create(name=name)
    return obj


def _get_or_create_worker(record: dict):
    ts_manager = record.get("ts_manager") or None
    ts_head = record.get("ts_head") or None
    client_manager = record.get("client_manager") or None
    client_head = record.get("client_head") or None

    if not any([ts_manager, ts_head, client_manager, client_head]):
        return None

    obj, _ = models.Worker.objects.get_or_create(
        ts_manager=ts_manager,
        ts_head=ts_head,
        client_manager=client_manager,
        client_head=client_head,
        defaults={"fe": None, "be": None, "creative": None, "qa": None, "pm": None},
    )
    return obj


def _upsert_conversions(campaign, conversions: list):
    if not conversions:
        return
    models.Conversion.objects.filter(campaign=campaign).delete()
    models.Conversion.objects.bulk_create([
        models.Conversion(
            campaign=campaign,
            operator=c.get("operator", ""),
            event=c.get("event", ""),
            count=c.get("count") or 0,
            revenue=c.get("revenue"),
            payout=c.get("payout"),
            payout_currency=c.get("payout_currency"),
            payout_start_date=c.get("payout_start_date") or None,
            payout_end_date=c.get("payout_end_date") or None,
            math=c.get("math"),
        )
        for c in conversions
    ])


def _upsert_record(record: dict, month_obj) -> bool:
    campaign_id = record.get("client_camp")
    if not campaign_id:
        logger.warning("Skipping record — missing campaign_id (client_camp): %s", record)
        return False

    client = _get_or_create_client(record.get("client"))
    country = _get_or_create_country(record.get("country"))
    category = _get_or_create_simple(models.Category, record.get("categoria"))
    creative = _get_or_create_simple(models.Creative, record.get("creativity"))
    platform = _get_or_create_simple(models.Platform, record.get("platform"))
    plat_owner = _get_or_create_simple(models.PlatOwner, record.get("plat_owner"))
    detail_type = _get_or_create_simple(models.DetailType, record.get("detail_type"))
    worker = _get_or_create_worker(record)

    campaign, _ = models.Campaign.objects.update_or_create(
        month=month_obj,
        campaign_id=str(campaign_id),
        defaults={
            "client": client,
            "country": country,
            "category": category,
            "creative": creative,
            "platform": platform,
            "plat_owner": plat_owner,
            "worker": worker,
            "detail_type": detail_type,
            "client_camp": bool(campaign_id),
            "invoice_google": record.get("invoice_google"),
        },
    )

    models.Metric.objects.update_or_create(
        campaign=campaign,
        defaults={
            "cpa": record.get("cpa"),
            "er_cpa": record.get("er_cpa"),
            "er_cost": record.get("er_cost"),
            "cost_ts": record.get("cost_ts"),
            "cost_ts_currency": record.get("cost_ts_currency"),
            "conv": record.get("conv"),
            "convs_google": record.get("convs_google"),
            "convs_mob": record.get("convs_mob"),
            "cost_eur": record.get("cost_eur"),
            "revenue_eur": record.get("revenue_eur"),
            "revenue": record.get("revenue"),
            "revenue_currency": record.get("revenue_currency"),
            "margin_eur": record.get("margin_eur"),
            "roi": record.get("roi"),
        },
    )

    _upsert_conversions(campaign, record.get("conversions", []))

    return True


@shared_task(name="core.tasks.fetch_last_month_stats")
def fetch_last_month_stats():
    today = date.today()
    first_of_month = today.replace(day=1)
    last_month = first_of_month - timedelta(days=1)
    return fetch_monthly_stats.delay(last_month.year, last_month.month)


@shared_task(
    bind=True,
    name="core.tasks.fetch_monthly_stats",
    max_retries=3,
    default_retry_delay=60,
)
def fetch_monthly_stats(self, year=None, month=None):
    today = date.today()
    year = year or today.year
    month = month or today.month

    logger.info("Fetching monthly stats for %d/%02d", year, month)

    try:
        service = CostsService()
        response = service.get_monthly_stats(year, month)
        records = response.get("data", {}).get("results", [])

        logger.info("Received %d records for %d/%02d", len(records), year, month)

        month_obj = _get_or_create_month(year, month)

        saved = 0
        errors = 0

        with transaction.atomic():
            for record in records:
                try:
                    if _upsert_record(record, month_obj):
                        saved += 1
                except Exception as exc:
                    logger.error("Failed to save record: %s | Error: %s", record, exc)
                    errors += 1

        result = {"year": year, "month": month, "saved": saved, "errors": errors}
        logger.info("Sync complete: %s", result)

        from core.tasks.exchange_rate_tasks import apply_exchange_rates_to_metrics
        apply_exchange_rates_to_metrics.delay(year=year, month=month)

        return result

    except Exception as exc:
        logger.error("Task failed for %d/%02d: %s", year, month, exc)
        raise self.retry(exc=exc)


@shared_task(
    bind=True,
    name="core.tasks.fetch_stats_range",
)
def fetch_stats_range(self, from_year, from_month, to_year, to_month):
    year, month = from_year, from_month
    results = []
    while (year, month) <= (to_year, to_month):
        task = fetch_monthly_stats.delay(year, month)
        results.append({"year": year, "month": month, "task_id": task.id})
        month += 1
        if month > 12:
            month = 1
            year += 1
    logger.info("Queued %d monthly sync tasks", len(results))
    return results
