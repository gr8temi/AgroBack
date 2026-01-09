import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models

class Farm(models.Model):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=10, unique=True, editable=False)
    owner = models.ForeignKey('User', on_delete=models.CASCADE, related_name='owned_farms')
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = str(uuid.uuid4())[:8].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class User(AbstractUser):
    ROLE_CHOICES = (
        ('staff', 'Staff'),
        ('manager', 'Manager'),
        ('financial_manager', 'Financial Manager'),
        ('superuser', 'Superuser'),
    )

    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='staff')
    farm = models.ForeignKey(Farm, on_delete=models.SET_NULL, null=True, blank=True, related_name='members')
    
    # Invitation system fields
    invitation_code = models.CharField(max_length=10, unique=True, null=True, blank=True)
    is_password_temporary = models.BooleanField(default=False)
    has_joined = models.BooleanField(default=False)  # Tracks if user accepted invitation
    
    # Password reset fields
    password_reset_token = models.CharField(max_length=6, null=True, blank=True)
    password_reset_token_expires = models.DateTimeField(null=True, blank=True)
    
    # Dynamic Permissions
    can_manage_flocks = models.BooleanField(default=False)
    can_manage_finances = models.BooleanField(default=False)
    can_manage_users = models.BooleanField(default=False)
    can_add_logs = models.BooleanField(default=False) # Staff can usually add logs

    def save(self, *args, **kwargs):
        # Auto-set permissions based on role if it's a new user or role changed
        # This provides good defaults while allowing overrides
        if self.role == 'superuser':
            self.can_manage_flocks = True
            self.can_manage_finances = True
            self.can_manage_users = True
            self.can_add_logs = True
        elif self.role == 'manager':
            self.can_manage_flocks = True
            self.can_manage_finances = True
            self.can_manage_users = False
            self.can_add_logs = True
        elif self.role == 'financial_manager':
            self.can_manage_flocks = False
            self.can_manage_finances = True
            self.can_manage_users = False
            self.can_add_logs = False
        elif self.role == 'staff':
            # Staff defaults: can view flocks (handled by view logic) and add logs
            # They shouldn't manage flocks/finances/users by default
            pass 
            
        super().save(*args, **kwargs)
