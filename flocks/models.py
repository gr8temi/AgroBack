from django.db import models
from core.models import User, Farm

class Flock(models.Model):
    name = models.CharField(max_length=100)
    breed = models.CharField(max_length=100)
    initial_quantity = models.PositiveIntegerField()
    current_quantity = models.PositiveIntegerField()
    date_added = models.DateField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='flocks', null=True, blank=True)

    def __str__(self):
        return self.name

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
    
    # For mortality, we might want to deduct from flock quantity automatically, 
    # but let's keep it simple for now and maybe handle in signals or view.
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
