import uuid
import secrets
from datetime import timedelta

from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.template.loader import render_to_string
from django.utils.html import strip_tags


def generate_invitation_code():
    """Generate a unique 8-character invitation code."""
    return secrets.token_urlsafe(6).upper()[:8]


def generate_temporary_password():
    """Generate a secure temporary password."""
    return secrets.token_urlsafe(12)


def generate_password_reset_token():
    """Generate a 6-digit password reset code."""
    return ''.join([str(secrets.randbelow(10)) for _ in range(6)])


def send_invitation_email(user, temp_password):
    """
    Send invitation email to new user with credentials.
    Uses mailcatcher in development for testing.
    """
    subject = f"Welcome to {user.farm.name}!"
    
    context = {
        'username': user.username,
        'farm_name': user.farm.name,
        'invitation_code': user.invitation_code,
        'temp_password': temp_password,
    }
    
    html_message = render_to_string('emails/invitation.html', context)
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
        print(f"✓ Invitation email sent to {user.email or 'no email'}")
        print(f"  View at: http://localhost:1080")
    except Exception as e:
        print(f"✗ Error sending email: {e}")
        # Log the details anyway for debugging
        print(f"\nInvitation Details for {user.username}:")
        print(f"  Code: {user.invitation_code}")
        print(f"  Temp Password: {temp_password}")


def send_password_reset_email(user, reset_token):
    """
    Send password reset email with reset token.
    Uses mailcatcher in development for testing.
    """
    subject = "Password Reset Request"
    
    context = {
        'username': user.username,
        'reset_token': reset_token,
    }
    
    html_message = render_to_string('emails/password_reset.html', context)
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
        print(f"✓ Password reset email sent to {user.email or 'no email'}")
        print(f"  View at: http://localhost:1080")
        print(f"  Token: {reset_token}")
    except Exception as e:
        print(f"✗ Error sending email: {e}")
        print(f"\nPassword Reset Token for {user.username}: {reset_token}")

