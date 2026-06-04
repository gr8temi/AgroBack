from datetime import date

from django.db import models
from django.db.models import Sum, Q

from core.models import User, Farm


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

    class Meta:
        indexes = [
            models.Index(fields=['farm', 'status']),
        ]

    def __str__(self):
        return self.name

    def compute_summary_stats(self):
        egg_agg = self.egg_collections.aggregate(total=Sum('quantity_collected'))
        self.total_eggs_collected = egg_agg['total'] or 0

        feed_agg = self.feed_logs.aggregate(
            total_kg=Sum('quantity_kg'),
            total_cost=Sum('cost'),
        )
        self.total_feed_kg = feed_agg['total_kg'] or 0
        self.total_feed_cost = feed_agg['total_cost'] or 0

        health_agg = self.health_logs.aggregate(
            total_cost=Sum('cost'),
            total_mortality=Sum('affected_birds', filter=Q(log_type='mortality')),
        )
        self.total_health_cost = health_agg['total_cost'] or 0
        self.total_mortality = health_agg['total_mortality'] or 0

        tx_agg = self.transactions.aggregate(
            income=Sum('amount', filter=Q(type='income')),
            expense=Sum('amount', filter=Q(type='expense')),
        )
        self.total_income = tx_agg['income'] or 0
        self.total_expense = tx_agg['expense'] or 0


class FeedLog(models.Model):
    flock = models.ForeignKey(Flock, on_delete=models.CASCADE, related_name='feed_logs')
    date = models.DateField()
    quantity_kg = models.DecimalField(max_digits=10, decimal_places=2)
    feed_type = models.CharField(max_length=100)
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

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
