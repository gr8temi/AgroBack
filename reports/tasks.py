import os
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import ReportConfig
from core.models import User
from core.utils import send_push_notification

@shared_task
def check_deadlines():
    """
    Checks for approaching deadlines (1 hour remaining) and passed deadlines.
    Sends notifications via Expo Push Notifications.
    """
    print("DEBUG: check_deadlines task started")
    now = timezone.now()
    # Simple logic: Find configs where deadline is soon
    # Note: deadline_time is just a TimeField, needs to be combined with Date
    # For now, let's just find configs enabled.
    
    configs = ReportConfig.objects.filter(is_enabled=True, deadline_time__isnull=False)
    print(f"DEBUG: Found {configs.count()} enabled report configs")
    
    for config in configs:
        # Construct deadline datetime for today
        deadline_time = config.deadline_time
        today = now.date()
        deadline_dt = timezone.datetime.combine(today, deadline_time)
        if timezone.is_aware(now):
            deadline_dt = timezone.make_aware(deadline_dt)
        
        # Check if 1 hour before (allow 5 min window for task execution)
        time_diff = deadline_dt - now
        print(f"DEBUG: Config {config.id} (Farm: {config.farm.name}) - Deadline: {deadline_dt}, Now: {now}, Diff: {time_diff}")
        
        # 1 Hour Reminder (Repeatedly notify during the last hour)
        if timedelta(minutes=0) < time_diff <= timedelta(minutes=60):
            print(f"DEBUG: Sending imminent deadline reminder for Farm {config.farm.name}")
            # Notify Staff AND Admins
            recipients = config.farm.members.filter(role__in=['staff', 'manager', 'superuser', 'admin'])
            
            message = f"Reminder: Daily Report is due soon ({deadline_time})."
            send_push_notification(recipients, "Report Deadline", message, data={'type': 'deadline_reminder', 'config_id': config.id})

        # Passed Deadline (e.g. 5 mins past)
        if timedelta(minutes=-5) >= time_diff >= timedelta(minutes=-15):
             print(f"DEBUG: Sending past deadline alert for Farm {config.farm.name}")
             # Notify Admin
             admins = config.farm.members.filter(role__in=['superuser', 'manager', 'admin']) 
             
             message = f"Alert: Daily Report deadline passed for {config.farm.name}."
             send_push_notification(admins, "Deadline Missed", message, data={'type': 'deadline_missed', 'config_id': config.id})

