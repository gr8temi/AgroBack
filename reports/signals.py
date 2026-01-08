from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import ReportConfig, Question
from .defaults import DEFAULT_QUESTIONS

@receiver(post_save, sender=ReportConfig)
def seed_default_questions(sender, instance, created, **kwargs):
    # Auto-seeding is disabled to allow users to select their own questions via the UI.
    pass
