import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

_BASE = "https://v6.exchangerate-api.com/v6"


def _get(url: str) -> dict:
    key = settings.EXCHANGE_RATE_API_KEY
    if not key:
        raise RuntimeError("EXCHANGE_RATE_API_KEY is not configured")
    full_url = f"{_BASE}/{key}/{url}"
    logger.info("GET %s", full_url)
    r = requests.get(full_url, timeout=15)
    r.raise_for_status()
    data = r.json()
    if data.get("result") != "success":
        raise RuntimeError(f"exchangerate-api error: {data.get('error-type', data)}")
    return data


def fetch_latest(base: str = "EUR") -> dict[str, float]:
    """Returns {currency: rate} where 1 base = rate currency."""
    data = _get(f"latest/{base}")
    return data["conversion_rates"]


def fetch_historical(year: int, month: int, day: int, base: str = "EUR") -> dict[str, float]:
    """Returns {currency: rate} for a specific calendar day."""
    data = _get(f"history/{base}/{year}/{month}/{day}")
    return data["conversion_rates"]
