import os
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import ReportConfig, DailyReport
from core.models import User
from core.utils import send_push_notification


def get_deadline_datetime(config, now):
    """
    Combines today's date with the config's deadline_time to produce
    a timezone-aware deadline datetime for the current day.
    """
    today = now.date()
    deadline_dt = timezone.datetime.combine(today, config.deadline_time)
    if timezone.is_aware(now):
        deadline_dt = timezone.make_aware(deadline_dt)
    return deadline_dt


def report_already_submitted(config, today):
    """
    Returns True if a DailyReport has already been submitted for this
    farm today, meaning no deadline reminders need to be sent.
    """
    return DailyReport.objects.filter(farm=config.farm, reference_date=today).exists()


def get_reminder_notification(time_diff):
    """
    Given the time difference (deadline - now), returns a (notification_type, message)
    tuple if we are inside a reminder window, or (None, None) if not.

    Windows:
      - 55–65 minutes before → 1-hour reminder
      - 25–35 minutes before → 30-minute reminder
    """
    if timedelta(minutes=55) <= time_diff <= timedelta(minutes=65):
        return (
            "deadline_reminder_60",
            f"Reminder: Daily Report is due in 1 hour.",
        )
    if timedelta(minutes=25) <= time_diff <= timedelta(minutes=35):
        return (
            "deadline_reminder_30",
            f"Reminder: Daily Report is due in 30 minutes.",
        )
    return None, None


def was_notified_today(config, now):
    """
    Returns True if a notification was already sent today AND within the
    last 20 minutes (debounce). Returns False if the last notification was
    on a previous day (so we always notify on each new day) or if the
    20-minute debounce window has elapsed.
    """
    if not config.last_notified_at:
        return False

    last_notified_local = config.last_notified_at
    if timezone.is_aware(last_notified_local):
        last_notified_local = timezone.localtime(last_notified_local)

    last_notified_date = last_notified_local.date()
    today_date = timezone.localtime(now).date()

    # Notified on a previous day → treat as "not yet notified today"
    if last_notified_date < today_date:
        return False

    # Same day: apply 20-minute debounce
    return (now - config.last_notified_at) < timedelta(minutes=20)


def send_reminder_notification(config, notification_type, message, now):
    """
    Sends a push notification to staff/manager/admin members of the farm
    and records the notification timestamp on the config.
    """
    recipients = config.farm.members.filter(
        role__in=["staff", "manager", "superuser", "admin"]
    )
    send_push_notification(
        recipients,
        "Report Deadline",
        message,
        data={"type": notification_type, "config_id": config.id},
    )
    config.last_notified_at = now
    config.save(update_fields=["last_notified_at"])


def handle_missed_deadline(config, time_diff, now):
    """
    If the deadline has just passed (between 5 and 15 minutes ago) and we
    haven't sent a missed-deadline alert recently, notifies admins/managers.
    """
    if not (timedelta(minutes=-15) <= time_diff <= timedelta(minutes=-5)):
        return

    # Debounce: skip if already notified within the last 20 minutes
    if config.last_notified_at and (
        now - config.last_notified_at < timedelta(minutes=20)
    ):
        return

    admins = config.farm.members.filter(role__in=["superuser", "manager", "admin"])
    message = f"Alert: Daily Report deadline passed for {config.farm.name}."
    send_push_notification(
        admins,
        "Deadline Missed",
        message,
        data={"type": "deadline_missed", "config_id": config.id},
    )
    config.last_notified_at = now
    config.save(update_fields=["last_notified_at"])


@shared_task
def check_deadlines():
    """
    Periodic task that checks every enabled ReportConfig and sends push
    notifications when a daily report deadline is approaching or has passed.
    """
    now = timezone.now()
    configs = ReportConfig.objects.filter(is_enabled=True, deadline_time__isnull=False)

    for config in configs:
        today = now.date()

        if report_already_submitted(config, today):
            continue

        deadline_dt = get_deadline_datetime(config, now)
        time_diff = deadline_dt - now

        # --- Upcoming deadline reminders (60-min and 30-min windows) ---
        notification_type, message = get_reminder_notification(time_diff)
        if notification_type and not was_notified_today(config, now):
            send_reminder_notification(config, notification_type, message, now)

        # --- Missed deadline alert ---
        handle_missed_deadline(config, time_diff, now)
