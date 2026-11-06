from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('reports/', views.reports_view, name='reports_list'),
    path('reports/<str:filename>/', views.view_single_report, name='view_single_report'),
    path('api/posts/', views.api_posts_list, name='api_posts'),
    path('api/weekly-review/', views.api_weekly_review, name='api_weekly_review'),
    path('api/send-email-reports/', views.api_send_email_reports, name='api_send_email_reports'),
    path('api/trigger-growth/', views.api_trigger_growth, name='api_trigger_growth'),
    path('api/research-topic/', views.api_research_topic, name='api_research_topic'),
    path('api/system-stats/', views.api_system_stats, name='api_system_stats'),
    path('api/services-status/', views.api_services_status, name='api_services_status'),
    path('api/service-action/', views.api_service_action, name='api_service_action'),
    path('api/run-maintenance/', views.api_run_maintenance, name='api_run_maintenance'),
]
