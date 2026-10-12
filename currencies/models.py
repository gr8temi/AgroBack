from django.db import models

from .constants import SUPPORTED_CURRENCIES


class ExchangeRate(models.Model):
    base_currency = models.CharField(max_length=3, choices=SUPPORTED_CURRENCIES)
    target_currency = models.CharField(max_length=3, choices=SUPPORTED_CURRENCIES)
    rate = models.DecimalField(max_digits=18, decimal_places=8)
    fetched_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['base_currency', 'target_currency']),
        ]
        ordering = ['-fetched_at']

    def __str__(self):
        return f"{self.base_currency}->{self.target_currency}: {self.rate}"
