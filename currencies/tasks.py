import logging

import requests
from celery import shared_task
from django.conf import settings

from .constants import SUPPORTED_CURRENCIES
from .models import ExchangeRate

logger = logging.getLogger(__name__)


@shared_task
def fetch_exchange_rates():
    base = 'USD'
    target_codes = [code for code, _ in SUPPORTED_CURRENCIES if code != base]

    api_url = getattr(
        settings, 'EXCHANGE_RATE_API_URL',
        'https://open.er-api.com/v6/latest',
    )
    url = f"{api_url}/{base}"

    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        logger.error("Failed to fetch exchange rates: %s", e)
        return

    rates_data = data.get('rates', {})
    if not rates_data:
        logger.warning("No rates returned from API")
        return

    rows = []
    for code in target_codes:
        rate = rates_data.get(code)
        if rate is not None:
            rows.append(ExchangeRate(
                base_currency=base,
                target_currency=code,
                rate=rate,
            ))

    ExchangeRate.objects.bulk_create(rows)
    logger.info("Fetched %d exchange rates from %s", len(rows), api_url)
