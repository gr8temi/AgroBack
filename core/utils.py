import uuid
import secrets
from datetime import timedelta

from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from exponent_server_sdk import (
    PushClient,
    PushMessage,
    PushServerError,
    PushTicketError,
)

from .models import PushToken


def generate_invitation_code():
    """Generate a unique 8-character invitation code."""
    return secrets.token_urlsafe(6).upper()[:8]


def generate_temporary_password():
    """Generate a secure temporary password."""
    return secrets.token_urlsafe(12)


def generate_password_reset_token():
    """Generate a secure password reset token."""
    return secrets.token_urlsafe(24)


def send_invitation_email(user, temp_password):
    """
    Send invitation email to new user with credentials.
    Uses mailcatcher in development for testing.
    """
    subject = f"Welcome to {user.farm.name}!"

    context = {
        "username": user.username,
        "farm_name": user.farm.name,
        "invitation_code": user.invitation_code,
        "temp_password": temp_password,
    }

    html_message = render_to_string("emails/invitation.html", context)
    plain_message = strip_tags(html_message)

    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email] if user.email else [],
            html_message=html_message,
            fail_silently=False,
        )
    except Exception as e:
        _logger.error("Error sending invitation email to %s: %s", user.username, e)


def send_password_reset_email(user, reset_token):
    """
    Send password reset email with reset token.
    Uses mailcatcher in development for testing.
    """
    subject = "Password Reset Request"

    context = {
        "username": user.username,
        "reset_token": reset_token,
    }

    html_message = render_to_string("emails/password_reset.html", context)
    plain_message = strip_tags(html_message)

    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email] if user.email else [],
            html_message=html_message,
            fail_silently=False,
        )
    except Exception as e:
        _logger.error("Error sending password reset email to %s: %s", user.username, e)


import logging

_logger = logging.getLogger(__name__)
_push_client = PushClient()


def send_push_notification(users, title, message, data=None):
    """
    Send Expo Push Notifications to a list of users.
    """
    push_tokens = list(
        PushToken.objects.filter(user__in=users).values_list("id", "token")
    )

    if not push_tokens:
        return

    push_messages = []
    token_id_map = {}
    for token_id, token_str in push_tokens:
        push_messages.append(
            PushMessage(
                to=token_str,
                title=title,
                body=message,
                data=data,
                sound="default",
            )
        )
        token_id_map[token_str] = token_id

    try:
        receipts = _push_client.publish_multiple(push_messages)
        invalid_ids = []
        for receipt in receipts:
            if receipt.status == "error" and receipt.details and receipt.details.get("error") == "DeviceNotRegistered":
                token_str = receipt.push_message.to if hasattr(receipt, "push_message") else None
                if token_str and token_str in token_id_map:
                    invalid_ids.append(token_id_map[token_str])
        if invalid_ids:
            PushToken.objects.filter(id__in=invalid_ids).delete()
    except PushServerError as exc:
        _logger.error("Push server error: %s", exc.errors)
    except Exception as exc:
        _logger.error("Error sending push notifications: %s", exc)
