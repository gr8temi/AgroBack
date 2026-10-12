from decimal import Decimal

from django.core.cache import cache

from .models import ExchangeRate


def get_exchange_rate(from_currency, to_currency):
    if from_currency == to_currency:
        return Decimal('1')

    cache_key = f"exchange_rate:{from_currency}:{to_currency}"
    cached = cache.get(cache_key)
    if cached is not None:
        return Decimal(str(cached))

    rate_obj = ExchangeRate.objects.filter(
        base_currency=from_currency,
        target_currency=to_currency,
    ).first()

    if rate_obj:
        cache.set(cache_key, str(rate_obj.rate), timeout=3600)
        return rate_obj.rate

    inverse = ExchangeRate.objects.filter(
        base_currency=to_currency,
        target_currency=from_currency,
    ).first()

    if inverse and inverse.rate != 0:
        computed = (Decimal('1') / inverse.rate).quantize(Decimal('0.00000001'))
        cache.set(cache_key, str(computed), timeout=3600)
        return computed

    # Cross-rate via USD: e.g. NGN->KES = NGN->USD * USD->KES
    if from_currency != 'USD' and to_currency != 'USD':
        try:
            to_usd = get_exchange_rate(from_currency, 'USD')
            from_usd = get_exchange_rate('USD', to_currency)
            cross = (to_usd * from_usd).quantize(Decimal('0.00000001'))
            cache.set(cache_key, str(cross), timeout=3600)
            return cross
        except ValueError:
            pass

    raise ValueError(f"No exchange rate found for {from_currency} -> {to_currency}")


def convert_amount(amount, from_currency, to_currency):
    if from_currency == to_currency:
        return amount
    rate = get_exchange_rate(from_currency, to_currency)
    return (amount * rate).quantize(Decimal('0.01'))
