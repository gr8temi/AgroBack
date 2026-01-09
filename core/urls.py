from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, FarmViewSet, RegisterFarmOwnerView, RegisterFarmMemberView, RegisterPushTokenView

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'farms', FarmViewSet, basename='farm')
router.register(r'register-owner', RegisterFarmOwnerView, basename='register-owner')
router.register(r'register-member', RegisterFarmMemberView, basename='register-member')
router.register(r'register-token', RegisterPushTokenView, basename='register-token')

urlpatterns = [
    path('', include(router.urls)),
]
