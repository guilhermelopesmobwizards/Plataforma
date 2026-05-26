import calendar
import logging
import time
from datetime import date, timedelta

from celery import shared_task
from django.db.models import Avg

from core import models
from core.services.exchange_rate_service import fetch_historical, fetch_latest

logger = logging.getLogger(__name__)


def _apply_rates_for_month(year: int, month: int, rate_map: dict) -> int:
    """
    Computes revenue_eur, cost_eur, margin_eur, roi for every Metric in
    the given month that is missing EUR values. Returns number of rows updated.
    """
    qs = (
        models.Metric.objects
        .select_related("campaign__month")
        .filter(
            campaign__month__month_date__year=year,
            campaign__month__month_date__month=month,
        )
    )

    updated = 0
    for metric in qs.iterator():
        changes = {}

        if metric.revenue is not None and metric.revenue_currency:
            cur = metric.revenue_currency
            if cur == "EUR":
                changes["revenue_eur"] = float(metric.revenue)
            else:
                rate = rate_map.get((year, month, cur))
                if rate:
                    changes["revenue_eur"] = float(metric.revenue) / rate

        if metric.cost_ts is not None and metric.cost_ts_currency:
            cur = metric.cost_ts_currency
            if cur == "EUR":
                changes["cost_eur"] = float(metric.cost_ts)
            else:
                rate = rate_map.get((year, month, cur))
                if rate:
                    changes["cost_eur"] = float(metric.cost_ts) / rate

        rev = changes.get("revenue_eur")
        if rev is None and metric.revenue_eur is not None:
            rev = float(metric.revenue_eur)
        cost = changes.get("cost_eur")
        if cost is None and metric.cost_eur is not None:
            cost = float(metric.cost_eur)
        if rev is not None and cost is not None:
            changes["margin_eur"] = rev - cost
            if cost != 0:
                changes["roi"] = changes["margin_eur"] / cost

        if changes:
            models.Metric.objects.filter(pk=metric.pk).update(**changes)
            updated += 1

    return updated


def _build_rate_map() -> dict:
    """Returns {(year, month, currency): float_rate} from ExchangeRate table."""
    return {
        (er.year, er.month, er.currency): float(er.rate)
        for er in models.ExchangeRate.objects.all()
    }


def _known_currencies() -> list[str]:
    """Distinct non-EUR currencies referenced anywhere in the data."""
    sources = [
        models.Conversion.objects.values_list("payout_currency", flat=True).distinct(),
        models.Metric.objects.values_list("revenue_currency", flat=True).distinct(),
        models.Metric.objects.values_list("cost_ts_currency", flat=True).distinct(),
        models.ConversionAdjustment.objects.values_list("payout_currency", flat=True).distinct(),
    ]
    seen = set()
    for qs in sources:
        seen.update(c for c in qs if c and c != "EUR")
    return list(seen)


def _upsert_daily(target_date: date, rates: dict[str, float], currencies: list[str]):
    saved = 0
    for currency in currencies:
        rate = rates.get(currency)
        if rate is None:
            logger.warning("No rate for %s on %s", currency, target_date)
            continue
        models.DailyExchangeRate.objects.update_or_create(
            date=target_date,
            currency=currency,
            defaults={"rate": rate},
        )
        saved += 1
    return saved


def _compute_and_store_average(year: int, month: int) -> dict:
    """
    Averages DailyExchangeRate rows for year/month and writes to ExchangeRate.
    Skips rows where ExchangeRate.is_locked is True.
    """
    results = {}
    rows = (
        models.DailyExchangeRate.objects
        .filter(date__year=year, date__month=month)
        .values("currency")
        .annotate(avg_rate=Avg("rate"))
    )
    for row in rows:
        currency = row["currency"]
        avg_rate = row["avg_rate"]
        # Skip if manually locked
        locked = models.ExchangeRate.objects.filter(
            year=year, month=month, currency=currency, is_locked=True
        ).exists()
        if locked:
            logger.info("Skipping locked ExchangeRate %s %d-%02d", currency, year, month)
            continue
        models.ExchangeRate.objects.update_or_create(
            year=year,
            month=month,
            currency=currency,
            defaults={"rate": avg_rate, "is_locked": False},
        )
        results[currency] = float(avg_rate)
    return results


@shared_task(
    bind=True,
    name="core.tasks.fetch_daily_rates",
    max_retries=3,
    default_retry_delay=300,
)
def fetch_daily_rates(self, target_date_str: str | None = None):
    """
    Fetches today's (or a specific day's) rates for all known currencies
    and stores them in DailyExchangeRate. Then recomputes the monthly average.
    """
    if target_date_str:
        target_date = date.fromisoformat(target_date_str)
    else:
        target_date = date.today()

    currencies = _known_currencies()
    if not currencies:
        logger.info("No currencies to fetch — skipping")
        return {"skipped": True}

    logger.info("Fetching rates for %s — currencies: %s", target_date, currencies)

    try:
        if target_date == date.today():
            rates = fetch_latest()
        else:
            rates = fetch_historical(target_date.year, target_date.month, target_date.day)
    except Exception as exc:
        logger.error("Failed to fetch rates for %s: %s", target_date, exc)
        raise self.retry(exc=exc)

    saved = _upsert_daily(target_date, rates, currencies)
    averages = _compute_and_store_average(target_date.year, target_date.month)

    rate_map = _build_rate_map()
    eur_updated = _apply_rates_for_month(target_date.year, target_date.month, rate_map)

    result = {
        "date": str(target_date),
        "currencies": currencies,
        "saved": saved,
        "monthly_averages": averages,
        "eur_metrics_updated": eur_updated,
    }
    logger.info("fetch_daily_rates complete: %s", result)
    return result


@shared_task(
    bind=True,
    name="core.tasks.compute_monthly_average",
)
def compute_monthly_average(self, year: int | None = None, month: int | None = None):
    """
    Computes the monthly average from DailyExchangeRate and stores in ExchangeRate.
    Called with no args by beat on the 1st of each month to finalise the previous month.
    """
    if year is None or month is None:
        # Default: previous month
        today = date.today()
        first = today.replace(day=1)
        prev = first - timedelta(days=1)
        year, month = prev.year, prev.month

    logger.info("Computing monthly average for %d-%02d", year, month)
    averages = _compute_and_store_average(year, month)
    logger.info("Monthly averages for %d-%02d: %s", year, month, averages)
    return {"year": year, "month": month, "averages": averages}


@shared_task(
    bind=True,
    name="core.tasks.backfill_exchange_rates",
)
def backfill_exchange_rates(self):
    """
    Backfills exchange rates for past months that have campaign data but no
    DailyExchangeRate rows.

    Historical endpoint requires a paid exchangerate-api.com plan. On the free
    plan this falls back to storing today's latest rate as a proxy for each
    missing month — imprecise but better than no data.
    """
    currencies = _known_currencies()
    if not currencies:
        logger.info("No currencies to backfill — skipping")
        return {"skipped": True}

    today = date.today()

    months = (
        models.Month.objects
        .filter(campaigns__isnull=False)
        .values_list("month_date__year", "month_date__month")
        .distinct()
        .order_by("month_date__year", "month_date__month")
    )

    # Fetch today's rates once — used as fallback for months with no daily data
    try:
        latest_rates = fetch_latest()
    except Exception as exc:
        logger.error("Could not fetch latest rates for backfill fallback: %s", exc)
        raise self.retry(exc=exc)

    total_fetched = 0
    total_skipped = 0
    errors = []

    for year, month in months:
        # Skip the current month — daily task handles it
        if (year, month) == (today.year, today.month):
            continue

        # Check if already have daily data for this month
        has_data = models.DailyExchangeRate.objects.filter(
            date__year=year,
            date__month=month,
            currency__in=currencies,
        ).exists()

        if has_data:
            total_skipped += 1
            _compute_and_store_average(year, month)
            continue

        # Try historical API (paid plan); fall back to latest rate
        _, days_in_month = calendar.monthrange(year, month)
        mid_day = min(15, days_in_month)  # use mid-month as representative day
        target = date(year, month, mid_day)

        try:
            rates = fetch_historical(year, month, mid_day)
            logger.info("Historical rates fetched for %s", target)
        except Exception:
            logger.warning(
                "Historical endpoint unavailable for %s — using today's rate as proxy", target
            )
            rates = latest_rates

        _upsert_daily(target, rates, currencies)
        _compute_and_store_average(year, month)
        total_fetched += 1
        time.sleep(0.5)

    # Apply EUR values to all metrics now that exchange rates are stored
    rate_map = _build_rate_map()
    eur_updated = 0
    for year, month in months:
        eur_updated += _apply_rates_for_month(year, month, rate_map)

    result = {
        "currencies": currencies,
        "fetched": total_fetched,
        "skipped": total_skipped,
        "errors": errors,
        "eur_metrics_updated": eur_updated,
    }
    logger.info("backfill_exchange_rates complete: %s", result)
    return result


@shared_task(name="core.tasks.apply_exchange_rates_to_metrics")
def apply_exchange_rates_to_metrics(year: int | None = None, month: int | None = None):
    """
    Standalone task: (re)compute EUR values on Metric rows using stored ExchangeRate.
    Pass year+month to target a specific month, or omit to process all months.
    """
    rate_map = _build_rate_map()

    if year and month:
        updated = _apply_rates_for_month(year, month, rate_map)
        return {"year": year, "month": month, "updated": updated}

    months = (
        models.Month.objects
        .filter(campaigns__isnull=False)
        .values_list("month_date__year", "month_date__month")
        .distinct()
    )
    total = 0
    for y, m in months:
        total += _apply_rates_for_month(y, m, rate_map)
    return {"updated": total}
