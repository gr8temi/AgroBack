
import os
import django
from datetime import timedelta
from django.utils import timezone
from unittest.mock import MagicMock, patch

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from reports.tasks import check_deadlines
from reports.models import ReportConfig
from core.models import Farm, User

def test_notification_recurrence():
    # Setup
    # Create valid user and farm
    # Use obscure names to avoid conflict
    email = "test_recurrence_user@example.com"
    if not User.objects.filter(email=email).exists():
        user = User.objects.create(email=email, password='password', first_name='Test', last_name='User')
    else:
        user = User.objects.get(email=email)
        
    farm_name = "Recurrence Test Farm"
    if not Farm.objects.filter(name=farm_name).exists():
        farm = Farm.objects.create(name=farm_name, owner=user)
        farm.members.add(user) # ensure user is member
    else:
        farm = Farm.objects.get(name=farm_name)

    # Clean up old configs
    ReportConfig.objects.filter(farm=farm).delete()

    now = timezone.now()
    # Set deadline to 1 hour from now (so we fall into 60 min window)
    deadline_time = (now + timedelta(hours=1)).time()
    
    config = ReportConfig.objects.create(
        farm=farm,
        is_enabled=True,
        deadline_time=deadline_time
    )

    # CASE 1: last_notified_at was 25 hours ago
    # Expected: Should notify
    config.last_notified_at = now - timedelta(hours=25)
    config.save()

    print(f"Setup: Now={now}, DeadlineTime={deadline_time}, LastNotified={config.last_notified_at}")

    # Mock send_push_notification to capture calls
    with patch('reports.tasks.send_push_notification') as mock_send:
        check_deadlines()
        
        if mock_send.called:
            print("SUCCESS: Notification sent when last_notified_at > 24h.")
        else:
            print("FAILURE: Notification NOT sent when last_notified_at > 24h.")
            
    # CASE 2: last_notified_at was 10 mins ago
    # Expected: Should NOT notify (debounce)
    config.refresh_from_db()
    # Reset last_notified_at manually to "now - 10 mins" (simulate we just ran)
    # But wait, check_deadlines updates last_notified_at if it runs correctly.
    # So let's force it.
    config.last_notified_at = now - timedelta(minutes=10)
    config.save()
    
    with patch('reports.tasks.send_push_notification') as mock_send:
        check_deadlines()
        
        if not mock_send.called:
            print("SUCCESS: Notification correctly skipped when last_notified_at < 20m.")
        else:
            print("FAILURE: Notification sent despite debounce!")

if __name__ == '__main__':
    try:
        test_notification_recurrence()
    except Exception as e:
        print(f"Error: {e}")
