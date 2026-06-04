import logging

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from datetime import timedelta

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import Farm, PushToken
from .utils import (
    generate_invitation_code,
    generate_temporary_password,
    send_invitation_email,
    generate_password_reset_token,
    send_password_reset_email,
)
from .permissions import IsSuperUser
from .serializers import (
    UserSerializer,
    FarmSerializer,
    CustomTokenObtainPairSerializer,
    PushTokenSerializer,
)

logger = logging.getLogger(__name__)


class AuthRateThrottle(AnonRateThrottle):
    rate = "5/minute"

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [IsSuperUser]

    def get_queryset(self):
        return User.objects.filter(farm=self.request.user.farm)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        # Generate invitation code and temporary password
        invitation_code = generate_invitation_code()
        temp_password = generate_temporary_password()

        # Modify request data to include generated fields
        data = request.data.copy()
        data["password"] = temp_password

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)

        # Create user with invitation fields
        user = serializer.save(
            farm=request.user.farm,
            invitation_code=invitation_code,
            is_password_temporary=True,
        )

        # Reload user to ensure farm relationship is loaded
        user.refresh_from_db()

        # Send invitation email (logs to console for now)
        send_invitation_email(user, temp_password)

        headers = self.get_success_headers(serializer.data)
        response_data = serializer.data
        response_data["invitation_code"] = invitation_code
        response_data["temporary_password"] = temp_password

        return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=False, methods=["post"], permission_classes=[AllowAny], throttle_classes=[AuthRateThrottle])
    def validate_invitation(self, request):
        """Validate invitation code and return user info."""
        code = request.data.get("invitation_code", None)
        if not code:
            return Response(
                {"error": "Invitation code is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(invitation_code=code)
            if user.farm:
                # Check if user has already joined
                already_joined = user.has_joined

                # Mark user as having joined only if it's their first time
                if not already_joined:
                    user.has_joined = True
                    user.save(update_fields=["has_joined"])

                return Response(
                    {
                        "valid": True,
                        "username": user.username,
                        "farm_name": user.farm.name,
                        "is_password_temporary": user.is_password_temporary,
                        "already_joined": already_joined,
                    }
                )
            else:
                return Response(
                    {"error": "Invalid invitation"}, status=status.HTTP_400_BAD_REQUEST
                )
        except User.DoesNotExist:
            return Response(
                {"error": "Invalid invitation code"}, status=status.HTTP_404_NOT_FOUND
            )

    @transaction.atomic
    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    def reset_password(self, request):
        """Reset password for user with temporary password."""
        new_password = request.data.get("new_password")
        if not new_password:
            return Response(
                {"error": "New password is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = request.user
        if not user.is_password_temporary:
            return Response(
                {"error": "Password reset not required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            validate_password(new_password, user)
        except ValidationError as e:
            return Response({"error": e.messages}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.is_password_temporary = False
        user.save()

        return Response({"message": "Password reset successfully"})

    @action(detail=False, methods=["post"], permission_classes=[AllowAny], throttle_classes=[AuthRateThrottle])
    def request_password_reset(self, request):
        """Request a password reset token via email."""
        username = request.data.get("username")
        if not username:
            return Response(
                {"error": "Username is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(username=username)

            # Generate reset token
            reset_token = generate_password_reset_token()
            user.password_reset_token = reset_token
            user.password_reset_token_expires = timezone.now() + timedelta(hours=1)
            user.save(
                update_fields=["password_reset_token", "password_reset_token_expires"]
            )

            # Send email
            send_password_reset_email(user, reset_token)

            return Response(
                {
                    "message": "Password reset instructions sent to your email",
                    "username": user.username,
                }
            )
        except User.DoesNotExist:
            # Don't reveal if user exists or not for security
            return Response(
                {
                    "message": "If the username exists, password reset instructions have been sent"
                }
            )

    @transaction.atomic
    @action(detail=False, methods=["post"], permission_classes=[AllowAny], throttle_classes=[AuthRateThrottle])
    def reset_password_with_token(self, request):
        """Reset password using a reset token."""
        reset_token = request.data.get("reset_token")
        new_password = request.data.get("new_password")

        if not reset_token or not new_password:
            return Response(
                {"error": "Reset token and new password are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(password_reset_token=reset_token)

            # Check if token has expired
            if user.password_reset_token_expires < timezone.now():
                return Response(
                    {"error": "Reset token has expired"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:
                validate_password(new_password, user)
            except ValidationError as e:
                return Response({"error": e.messages}, status=status.HTTP_400_BAD_REQUEST)

            user.set_password(new_password)
            user.password_reset_token = None
            user.password_reset_token_expires = None
            user.save()

            return Response(
                {
                    "message": "Password reset successfully. You can now login with your new password."
                }
            )
        except User.DoesNotExist:
            return Response(
                {"error": "Invalid reset token"}, status=status.HTTP_404_NOT_FOUND
            )

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        """Override destroy to prevent deleting the last superuser."""
        user = self.get_object()
        farm = user.farm

        # Check if this user is a superuser
        if user.role == "superuser":
            # Count total superusers in the farm
            superuser_count = User.objects.filter(farm=farm, role="superuser").count()

            if superuser_count <= 1:
                return Response(
                    {
                        "error": "Cannot delete the last superuser",
                        "message": "You must either transfer ownership to another user or delete the farm",
                        "is_last_superuser": True,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Proceed with deletion
        return super().destroy(request, *args, **kwargs)

    @transaction.atomic
    @action(detail=True, methods=["post"], permission_classes=[IsSuperUser])
    def transfer_ownership(self, request, pk=None):
        """Transfer farm ownership to another user and delete current superuser."""
        current_user = self.get_object()
        if current_user != request.user:
            return Response(
                {"error": "You can only transfer ownership from your own account"},
                status=status.HTTP_403_FORBIDDEN,
            )
        new_superuser_id = request.data.get("new_superuser_id")

        if not new_superuser_id:
            return Response(
                {"error": "New superuser ID is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if current user is a superuser
        if current_user.role != "superuser":
            return Response(
                {"error": "Only superusers can transfer ownership"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            new_superuser = User.objects.get(
                id=new_superuser_id, farm=current_user.farm
            )
        except User.DoesNotExist:
            return Response(
                {"error": "New superuser not found in this farm"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Update new superuser
        new_superuser.role = "superuser"
        new_superuser.can_manage_flocks = True
        new_superuser.can_manage_finances = True
        new_superuser.can_manage_users = True
        new_superuser.can_add_logs = True
        new_superuser.save()

        # Update farm owner
        farm = current_user.farm
        farm.owner = new_superuser
        farm.save()

        # Delete current user
        current_user.delete()

        return Response(
            {
                "message": "Ownership transferred successfully",
                "new_superuser": new_superuser.username,
            }
        )


class FarmViewSet(viewsets.ModelViewSet):
    serializer_class = FarmSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "head", "options", "post"]

    def get_queryset(self):
        if self.request.user.farm:
            return Farm.objects.filter(id=self.request.user.farm_id)
        return Farm.objects.none()

    @transaction.atomic
    @action(detail=False, methods=["post"])
    def create_farm(self, request):
        name = request.data.get("name")
        if not name:
            return Response(
                {"error": "Farm name is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        if request.user.farm:
            return Response(
                {"error": "User already belongs to a farm"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        farm = Farm.objects.create(name=name, owner=request.user)

        # Update user role to superuser and assign farm
        request.user.farm = farm
        request.user.role = "superuser"
        request.user.save()  # This will trigger the save method to update permissions

        return Response(FarmSerializer(farm).data, status=status.HTTP_201_CREATED)

    @transaction.atomic
    @action(detail=False, methods=["post"])
    def join_farm(self, request):
        code = request.data.get("code")
        if not code:
            return Response(
                {"error": "Invitation code is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if request.user.farm:
            return Response(
                {"error": "User already belongs to a farm"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            farm = Farm.objects.get(code=code)
        except Farm.DoesNotExist:
            return Response(
                {"error": "Invalid invitation code"}, status=status.HTTP_404_NOT_FOUND
            )

        request.user.farm = farm
        request.user.save()

        return Response(FarmSerializer(farm).data, status=status.HTTP_200_OK)

    @transaction.atomic
    @action(detail=False, methods=["post"], permission_classes=[IsSuperUser])
    def delete_farm(self, request):
        """Delete the farm and all associated data. Superuser only."""
        user = request.user
        farm = user.farm

        if not farm:
            return Response(
                {"error": "No farm associated with user"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Verify user is superuser
        if user.role != "superuser":
            return Response(
                {"error": "Only superusers can delete farms"},
                status=status.HTTP_403_FORBIDDEN,
            )

        farm_name = farm.name

        # Delete farm (cascades to all related data)
        farm.delete()

        return Response(
            {
                "message": f'Farm "{farm_name}" and all associated data deleted successfully'
            }
        )


class RegisterFarmOwnerView(viewsets.GenericViewSet):
    permission_classes = [AllowAny]
    serializer_class = UserSerializer  # We can use a specific serializer if needed

    @transaction.atomic
    @action(detail=False, methods=["post"])
    def register(self, request):
        # Expects: username, password, email, farm_name
        username = request.data.get("username")
        password = request.data.get("password")
        email = request.data.get("email")
        farm_name = request.data.get("farm_name")

        if not all([username, password, farm_name]):
            return Response(
                {"error": "Username, password, and farm name are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if User.objects.filter(username=username).exists():
            return Response(
                {"error": "Username already exists"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Create User
        user = User.objects.create_user(
            username=username, email=email, password=password, role="superuser"
        )

        # Create Farm
        farm = Farm.objects.create(name=farm_name, owner=user)

        # Link User to Farm
        user.farm = farm
        user.save()

        # Generate Tokens
        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "username": user.username,
                "role": user.role,
                "permissions": {
                    "can_manage_flocks": user.can_manage_flocks,
                    "can_manage_finances": user.can_manage_finances,
                    "can_manage_users": user.can_manage_users,
                    "can_add_logs": user.can_add_logs,
                },
                "farm": FarmSerializer(farm).data,
            },
            status=status.HTTP_201_CREATED,
        )


class RegisterFarmMemberView(viewsets.GenericViewSet):
    permission_classes = [AllowAny]
    serializer_class = UserSerializer

    @transaction.atomic
    @action(detail=False, methods=["post"])
    def register(self, request):
        # Expects: username, password, email, farm_code
        username = request.data.get("username")
        password = request.data.get("password")
        email = request.data.get("email")
        farm_code = request.data.get("farm_code")

        if not all([username, password, farm_code]):
            return Response(
                {"error": "Username, password, and farm code are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if User.objects.filter(username=username).exists():
            return Response(
                {"error": "Username already exists"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            farm = Farm.objects.get(code=farm_code)
        except Farm.DoesNotExist:
            return Response(
                {"error": "Invalid farm code"}, status=status.HTTP_404_NOT_FOUND
            )

        # Create User (Default role: staff)
        user = User.objects.create_user(
            username=username, email=email, password=password, role="staff"
        )

        # Link User to Farm
        user.farm = farm
        user.save()

        # Generate Tokens
        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "username": user.username,
                "role": user.role,
                "permissions": {
                    "can_manage_flocks": user.can_manage_flocks,
                    "can_manage_finances": user.can_manage_finances,
                    "can_manage_users": user.can_manage_users,
                    "can_add_logs": user.can_add_logs,
                },
                "farm": FarmSerializer(farm).data,
            },
            status=status.HTTP_201_CREATED,
        )


class CustomTokenObtainPairView(TokenObtainPairView):
    permission_classes = [AllowAny]
    serializer_class = CustomTokenObtainPairSerializer
    throttle_classes = [AuthRateThrottle]


class RegisterPushTokenView(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def create(self, request):
        token_str = request.data.get("token")

        if not token_str:
            return Response(
                {"error": "Token is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        PushToken.objects.update_or_create(
            token=token_str, defaults={"user": request.user}
        )

        # Clean up old tokens for this user (keep last 5)
        user_tokens = PushToken.objects.filter(user=request.user).order_by("-created_at")
        stale_ids = user_tokens[5:].values_list("id", flat=True)
        PushToken.objects.filter(id__in=list(stale_ids)).delete()

        return Response({"status": "success"}, status=status.HTTP_201_CREATED)
