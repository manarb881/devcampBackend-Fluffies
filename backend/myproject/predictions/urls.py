from django.urls import path
from .views import StockPredictionCreateView, StockPredictionListView

urlpatterns = [
    path('predictions/', StockPredictionCreateView.as_view(), name='stock-prediction-create'),
    path('predictions/list/', StockPredictionListView.as_view(), name='stock-prediction-list'),
]