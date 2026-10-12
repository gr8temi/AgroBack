from django.db import models

from core.models import User, Farm
from currencies.constants import SUPPORTED_CURRENCIES, DEFAULT_CURRENCY

class Transaction(models.Model):
    TRANSACTION_TYPES = (
        ('income', 'Income'),
        ('expense', 'Expense'),
    )
    CATEGORIES = (
        # Expense categories
        ('feed', 'Feed'),
        ('medication', 'Medication'),
        ('equipment', 'Equipment'),
        ('labor', 'Labor'),
        ('utilities', 'Utilities'),
        ('bird_purchase', 'Bird Purchase'),
        # Income categories
        ('egg_sales', 'Egg Sales'),
        ('bird_sales', 'Bird Sales'),
        ('manure_sales', 'Manure Sales'),
        # Common
        ('other', 'Other'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='transactions', null=True, blank=True)
    date = models.DateField()
    type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    category = models.CharField(max_length=50, choices=CATEGORIES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, choices=SUPPORTED_CURRENCIES, default=DEFAULT_CURRENCY)
    original_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    original_currency = models.CharField(max_length=3, null=True, blank=True)
    description = models.TextField(blank=True)
    
    # Optional link to specific flock if applicable
    related_flock = models.ForeignKey('flocks.Flock', on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
    invoice = models.ForeignKey('invoices.Invoice', on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
    client_id = models.UUIDField(unique=True, null=True, blank=True)

    def __str__(self):
        return f"{self.type} - {self.category} - {self.amount}"
