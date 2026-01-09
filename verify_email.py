from django.contrib.auth import get_user_model
from core.models import Farm
from core.utils import send_invitation_email, send_password_reset_email

User = get_user_model()

# Create dummy data for testing email
try:
    user = User.objects.get(username='test_email_user')
except User.DoesNotExist:
    user = User.objects.create_user('test_email_user', 'test_email@example.com', 'password')
    farm, _ = Farm.objects.get_or_create(name='Test Farm', owner=user)
    user.farm = farm
    user.invitation_code = 'TESTCODE'
    user.save()

print("Sending Invitation Email...")
send_invitation_email(user, 'temp_password_123')

print("\nSending Password Reset Email...")
send_password_reset_email(user, '123456')
