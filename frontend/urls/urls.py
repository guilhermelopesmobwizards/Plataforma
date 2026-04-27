from django.urls import path
from ..views import views

urlpatterns = [
    path("", views.dashboard_view, name="dashboard"),
    path("campaigns/", views.campaign_list_view, name="campaign-list"),
    path("campaigns/<int:pk>/", views.campaign_detail_view, name="campaign-detail"),
    path("metrics/", views.metrics_view, name="metrics"),
    path("comparisons/", views.comparisons_view, name="comparisons"),
    path("clients/", views.clients_view, name="clients"),
    path("worker/", views.workers_view, name="worker"),
    path("platforms/", views.platforms_view, name="platforms"),
    path("configurations/", views.configurations_view, name="configurations"),
    # --- JSON endpoints ---
    path("api/campaigns/", views.api_campaigns, name="api-campaigns"),
    path(
        "api/campaigns/<int:pk>/", views.api_campaign_detail, name="api-campaign-detail"
    ),
    path("api/dashboard/", views.api_dashboard, name="api-dashboard"),
    path("api/metrics/", views.api_metrics, name="api_metrics"),
    path("api/comparisons/", views.api_comparisons, name="api_comparisons"),
    # --- Import ---
    path("api/import/excel/", views.ExcelImportView.as_view(), name="import-excel"),
]
