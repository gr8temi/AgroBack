import uuid
import secrets
from datetime import timedelta

from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone


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
    
    message = f"""Hello {user.username},

You have been invited to join {user.farm.name}.

Your credentials:
  Invitation Code: {user.invitation_code}
  Temporary Password: {temp_password}

To get started:
1. Open the app and click 'Join Farm'
2. Enter your invitation code: {user.invitation_code}
3. Login with username '{user.username}' and the temporary password
4. You will be prompted to reset your password

Welcome aboard!
"""
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email] if user.email else [],
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
    
    # Token expires in 1 hour
    expires_at = timezone.now() + timedelta(hours=1)
    
    message = f"""Hello {user.username},

You requested a password reset for your account.

Your password reset token: {reset_token}

This token will expire in 1 hour.

To reset your password:
1. Open the app
2. Click 'Forgot Password'
3. Enter this token: {reset_token}
4. Set your new password

If you didn't request this reset, please ignore this email.
"""
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email] if user.email else [],
            fail_silently=False,
        )
        print(f"✓ Password reset email sent to {user.email or 'no email'}")
        print(f"  View at: http://localhost:1080")
        print(f"  Token: {reset_token}")
    except Exception as e:
        print(f"✗ Error sending email: {e}")
        print(f"\nPassword Reset Token for {user.username}: {reset_token}")

