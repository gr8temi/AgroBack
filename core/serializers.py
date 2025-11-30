from django.contrib.auth import get_user_model

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import Farm

User = get_user_model()

class FarmSerializer(serializers.ModelSerializer):
    class Meta:
        model = Farm
        fields = ('id', 'name', 'code', 'owner', 'created_at')
        read_only_fields = ('code', 'owner', 'created_at')

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    farm = FarmSerializer(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'role', 'password', 'farm', 'has_joined', 'can_manage_flocks', 'can_manage_finances', 'can_manage_users', 'can_add_logs')
        read_only_fields = ('has_joined',)

    def create(self, validated_data):
        # Extract fields that may be passed via save() but not in validated_data
        farm = validated_data.pop('farm', None)
        invitation_code = validated_data.pop('invitation_code', None)
        is_password_temporary = validated_data.pop('is_password_temporary', False)
        
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
            role=validated_data.get('role', 'staff'),
            can_manage_flocks=validated_data.get('can_manage_flocks', False),
            can_manage_finances=validated_data.get('can_manage_finances', False),
            can_manage_users=validated_data.get('can_manage_users', False),
            can_add_logs=validated_data.get('can_add_logs', True),
            farm=farm,
            invitation_code=invitation_code,
            is_password_temporary=is_password_temporary
        )
        return user

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data['role'] = self.user.role
        data['username'] = self.user.username
        data['is_password_temporary'] = self.user.is_password_temporary
        data['permissions'] = {
            'can_manage_flocks': self.user.can_manage_flocks,
            'can_manage_finances': self.user.can_manage_finances,
            'can_manage_users': self.user.can_manage_users,
            'can_add_logs': self.user.can_add_logs,
        }
        if self.user.farm:
            data['farm'] = FarmSerializer(self.user.farm).data
        else:
            data['farm'] = None
        return data
