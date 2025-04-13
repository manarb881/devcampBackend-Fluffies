
from django.urls import path
from .views import TrackOrder

urlpatterns = [
    path('order/<int:order_id>/', TrackOrder.as_view(), name='track-order'),
]