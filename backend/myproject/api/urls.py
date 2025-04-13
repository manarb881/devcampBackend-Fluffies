from django.urls import path
from .views import StripePaymentIntent, StoreStats, StripeWebhook

urlpatterns = [
    path('create-payment-intent/', StripePaymentIntent.as_view(), name='create-payment-intent'),
    path('store-stats/', StoreStats.as_view(), name='store-stats'),
    path('webhook/stripe/', StripeWebhook.as_view(), name='stripe-webhook'),
]