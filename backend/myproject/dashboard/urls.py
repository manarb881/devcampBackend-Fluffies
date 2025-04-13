
from django.urls import path
from .views import DashboardOverview, CustomersList, OrdersAnalytics, ProductAnalytics

urlpatterns = [
    path('overview/', DashboardOverview.as_view(), name='dashboard-overview'),
    path('customers/', CustomersList.as_view(), name='dashboard-customers'),
    path('orders-analytics/', OrdersAnalytics.as_view(), name='orders-analytics'),
    path('product-analytics/', ProductAnalytics.as_view(), name='product-analytics'),
]