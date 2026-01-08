import socketio
import os
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import ReportConfig
from core.models import User
from core.models import User

@shared_task
def check_deadlines():
    """
    Checks for approaching deadlines (1 hour remaining) and passed deadlines.
    Sends notifications via WebSockets.
    """
    print("DEBUG: check_deadlines task started")
    now = timezone.now()
    # Simple logic: Find configs where deadline is soon
    # Note: deadline_time is just a TimeField, needs to be combined with Date
    # For now, let's just find configs enabled.
    
    configs = ReportConfig.objects.filter(is_enabled=True, deadline_time__isnull=False)
    print(f"DEBUG: Found {configs.count()} enabled report configs")
    print(os.environ.get('CELERY_BROKER_URL', 'redis://redis:6379/0'), "CELERY_BROKER_URL")
    
    channel_layer = get_channel_layer()
    
    # Setup Socket.IO manager once
    mgr = socketio.RedisManager(os.environ.get('CELERY_BROKER_URL', 'redis://redis:6379/0'), write_only=True)
    sio = socketio.Server(client_manager=mgr)

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
            for member in recipients:
                print(f"DEBUG: Emitting to user_{member.id}")
                sio.emit('notification', {'message': f"Reminder: Daily Report is due soon ({deadline_time})."}, room=f"user_{member.id}")

        # Passed Deadline (e.g. 5 mins past)
        if timedelta(minutes=-5) >= time_diff >= timedelta(minutes=-15):
             print(f"DEBUG: Sending past deadline alert for Farm {config.farm.name}")
             # Notify Admin
             admins = config.farm.members.filter(role__in=['superuser', 'manager', 'admin']) 
             for admin in admins:
                print(f"DEBUG: Emitting to user_{admin.id}")
                mgr = socketio.RedisManager(os.environ.get('CELERY_BROKER_URL', 'redis://redis:6379/0'), write_only=True)
                mgr.emit('notification', {'message': f"Alert: Daily Report deadline passed for {config.farm.name}."}, room=f"user_{admin.id}")

