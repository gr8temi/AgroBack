from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TransactionViewSet, finance_categories

router = DefaultRouter()
router.register(r'transactions', TransactionViewSet, basename='transaction')

urlpatterns = [
    path('finance-categories/', finance_categories, name='finance-categories'),
    path('', include(router.urls)),
]
