import os
import django
from django.utils import timezone
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from reports.models import ReportConfig

now = timezone.now()
print(f"Current Time: {now}")

configs = ReportConfig.objects.filter(is_enabled=True, deadline_time__isnull=False)
print(f"Found {configs.count()} enabled configs")

for config in configs:
    deadline_time = config.deadline_time
    today = now.date()
    deadline_dt = timezone.datetime.combine(today, deadline_time)
    if timezone.is_aware(now):
        deadline_dt = timezone.make_aware(deadline_dt)
    
    time_diff = deadline_dt - now
    print(f"Config {config.id}: Deadline {deadline_dt}, Diff {time_diff}")
    
    if timedelta(minutes=0) < time_diff <= timedelta(minutes=60):
        print(" -> MATCHES 1-hour criteria")
    else:
        print(" -> DOES NOT MATCH criteria")
