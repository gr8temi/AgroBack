from datetime import date

from django.db import models
from django.db.models import Sum, Q

from core.models import User, Farm
from currencies.constants import SUPPORTED_CURRENCIES, DEFAULT_CURRENCY


class Flock(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('closed', 'Closed'),
    )
    CLOSURE_REASON_CHOICES = (
        ('sold', 'Sold'),
        ('culled', 'Culled'),
        ('disposed', 'Disposed'),
        ('transferred', 'Transferred'),
        ('other', 'Other'),
    )

    name = models.CharField(max_length=100)
    breed = models.CharField(max_length=100)
    initial_quantity = models.PositiveIntegerField()
    current_quantity = models.PositiveIntegerField()
    date_added = models.DateField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='flocks', null=True, blank=True)

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    closure_reason = models.CharField(max_length=20, choices=CLOSURE_REASON_CHOICES, null=True, blank=True)
    closure_notes = models.TextField(blank=True, default='')

    total_eggs_collected = models.PositiveIntegerField(default=0)
    total_feed_kg = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_feed_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_health_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_mortality = models.PositiveIntegerField(default=0)
    total_income = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_expense = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, choices=SUPPORTED_CURRENCIES, default=DEFAULT_CURRENCY)

    class Meta:
        indexes = [
            models.Index(fields=['farm', 'status']),
        ]

    def __str__(self):
        return self.name

    def compute_summary_stats(self):
        from decimal import Decimal
        from currencies.utils import convert_amount

        farm_currency = self.farm.base_currency if self.farm else DEFAULT_CURRENCY
        self.currency = farm_currency

        egg_agg = self.egg_collections.aggregate(total=Sum('quantity_collected'))
        self.total_eggs_collected = egg_agg['total'] or 0

        total_feed_kg = Decimal('0')
        total_feed_cost = Decimal('0')
        for log in self.feed_logs.all():
            total_feed_kg += log.quantity_kg
            total_feed_cost += convert_amount(log.cost, log.currency, farm_currency)
        self.total_feed_kg = total_feed_kg
        self.total_feed_cost = total_feed_cost

        total_health_cost = Decimal('0')
        total_mortality = 0
        for log in self.health_logs.all():
            total_health_cost += convert_amount(log.cost, log.currency, farm_currency)
            if log.log_type == 'mortality':
                total_mortality += log.affected_birds
        self.total_health_cost = total_health_cost
        self.total_mortality = total_mortality

        total_income = Decimal('0')
        total_expense = Decimal('0')
        for tx in self.transactions.all():
            converted = convert_amount(tx.amount, tx.currency, farm_currency)
            if tx.type == 'income':
                total_income += converted
            else:
                total_expense += converted
        self.total_income = total_income
        self.total_expense = total_expense


class FeedLog(models.Model):
    flock = models.ForeignKey(Flock, on_delete=models.CASCADE, related_name='feed_logs')
    date = models.DateField()
    quantity_kg = models.DecimalField(max_digits=10, decimal_places=2)
    feed_type = models.CharField(max_length=100)
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    currency = models.CharField(max_length=3, choices=SUPPORTED_CURRENCIES, default=DEFAULT_CURRENCY)
    original_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    original_currency = models.CharField(max_length=3, null=True, blank=True)

    def __str__(self):
        return f"{self.flock.name} - {self.date} - {self.feed_type}"

class HealthLog(models.Model):
    LOG_TYPES = (
        ('vaccination', 'Vaccination'),
        ('medication', 'Medication'),
        ('mortality', 'Mortality'),
        ('other', 'Other'),
    )
    flock = models.ForeignKey(Flock, on_delete=models.CASCADE, related_name='health_logs')
    date = models.DateField()
    log_type = models.CharField(max_length=20, choices=LOG_TYPES)
    description = models.TextField()
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    currency = models.CharField(max_length=3, choices=SUPPORTED_CURRENCIES, default=DEFAULT_CURRENCY)
    original_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    original_currency = models.CharField(max_length=3, null=True, blank=True)
    affected_birds = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.flock.name} - {self.log_type} - {self.date}"

class EggCollection(models.Model):
    flock = models.ForeignKey(Flock, on_delete=models.CASCADE, related_name='egg_collections')
    date = models.DateField()
    quantity_collected = models.PositiveIntegerField()
    damaged = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.flock.name} - {self.date} - {self.quantity_collected}"
