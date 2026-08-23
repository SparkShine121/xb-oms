from django.urls import path

from .views import FactorySummaryView, OverviewView, SalesSummaryView, TrackingSummaryView

urlpatterns = [
    path('sales/', SalesSummaryView.as_view()),
    path('factory-summary/', FactorySummaryView.as_view()),
    path('tracking-summary/', TrackingSummaryView.as_view()),
    path('overview/', OverviewView.as_view()),
]
