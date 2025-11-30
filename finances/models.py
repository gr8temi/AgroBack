from django.db import models
from core.models import User, Farm

class Transaction(models.Model):
    TRANSACTION_TYPES = (
        ('income', 'Income'),
        ('expense', 'Expense'),
    )
    CATEGORIES = (
        ('feed', 'Feed'),
        ('birds', 'Birds'),
        ('eggs', 'Eggs'),
        ('medication', 'Medication'),
        ('equipment', 'Equipment'),
        ('labor', 'Labor'),
        ('other', 'Other'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='transactions', null=True, blank=True)
    date = models.DateField()
    type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    category = models.CharField(max_length=50, choices=CATEGORIES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField(blank=True)
    
    # Optional link to specific flock if applicable
    related_flock = models.ForeignKey('flocks.Flock', on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')

    def __str__(self):
        return f"{self.type} - {self.category} - {self.amount}"
