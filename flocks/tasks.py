from celery import shared_task

from .models import Flock


@shared_task
def refresh_active_flock_stats():
    """Recompute cached summary stats for all active flocks."""
    for flock in Flock.objects.filter(status='active'):
        flock.compute_summary_stats()
        flock.save(update_fields=[
            'total_eggs_collected', 'total_feed_kg', 'total_feed_cost',
            'total_health_cost', 'total_mortality',
            'total_income', 'total_expense',
        ])
