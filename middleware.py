import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class CostsService:

    def __init__(self):
        self.token = settings.COSTS_API_TOKEN
        self.base_uri = settings.COSTS_API_BASE_URL

    def get_monthly_stats(self, year, month):
        return self.get(f"monthly-stats/{year}/{month:02d}/")

    def get(self, url, params={}, headers={}):
        full_url = f"{self.base_uri}/{url}"
        headers = {**headers, "Authorization": f"Token {self.token}"}

        logger.info("GET %s", full_url)

        r = requests.get(full_url, params=params, headers=headers)

        logger.info("Response [%s]: %s", r.status_code, r.text[:200])

        r.raise_for_status()
        return r.json()
