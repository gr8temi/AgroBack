from django.urls import path

from . import views

urlpatterns = [
    path('currencies/', views.supported_currencies, name='supported-currencies'),
    path('exchange-rates/', views.latest_exchange_rates, name='exchange-rates'),
]
