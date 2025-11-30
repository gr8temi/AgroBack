from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, FarmViewSet, RegisterFarmOwnerView, RegisterFarmMemberView

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'farms', FarmViewSet, basename='farm')
router.register(r'register-owner', RegisterFarmOwnerView, basename='register-owner')
router.register(r'register-member', RegisterFarmMemberView, basename='register-member')

urlpatterns = [
    path('', include(router.urls)),
]
