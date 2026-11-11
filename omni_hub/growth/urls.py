from django.urls import path
from . import views

urlpatterns = [
    # Authentication & Lock Screen
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('api/auth/login/', views.api_auth_login, name='api_auth_login'),
    path('api/auth/logout/', views.api_auth_logout, name='api_auth_logout'),

    path('', views.dashboard_view, name='dashboard'),
    path('reports/', views.reports_view, name='reports_list'),
    path('reports/<str:filename>/', views.view_single_report, name='view_single_report'),
    path('api/posts/', views.api_posts_list, name='api_posts'),
    path('api/weekly-review/', views.api_weekly_review, name='api_weekly_review'),
    path('api/send-email-reports/', views.api_send_email_reports, name='api_send_email_reports'),
    path('api/trigger-growth/', views.api_trigger_growth, name='api_trigger_growth'),
    path('api/research-topic/', views.api_research_topic, name='api_research_topic'),
    path('api/system-stats/', views.api_system_stats, name='api_system_stats'),
    path('api/health/', views.api_system_health, name='api_system_health'),
    path('api/wallet/stats/', views.api_wallet_stats, name='api_wallet_stats'),
    path('api/service-logs/<str:service_id>/', views.api_service_logs, name='api_service_logs'),
    path('api/services-status/', views.api_services_status, name='api_services_status'),
    path('api/services/register/', views.api_register_service, name='api_register_service'),
    path('api/services/delete/', views.api_delete_service, name='api_delete_service'),
    path('api/service-action/', views.api_service_action, name='api_service_action'),
    path('api/run-maintenance/', views.api_run_maintenance, name='api_run_maintenance'),
    path('api/dispatch-laptop/', views.api_dispatch_laptop, name='api_dispatch_laptop'),
    
    # OmniVault UI & Multimodal APIs
    path('vault/', views.vault_dashboard_view, name='vault_dashboard'),
    path('api/vault/categories/', views.api_vault_categories, name='api_vault_categories'),
    path('api/vault/list/', views.api_vault_list, name='api_vault_list'),
    path('api/vault/<int:resource_id>/', views.api_vault_detail, name='api_vault_detail'),
    path('api/vault/ingest/image/', views.api_vault_ingest_image, name='api_vault_ingest_image'),
    path('api/vault/ingest/url/', views.api_vault_ingest_url, name='api_vault_ingest_url'),
    path('api/vault/ingest/text/', views.api_vault_ingest_text, name='api_vault_ingest_text'),
    path('api/vault/ingest/pdf/', views.api_vault_ingest_pdf, name='api_vault_ingest_pdf'),
    path('api/vault/chat/', views.api_vault_chat, name='api_vault_chat'),
    path('api/vault/toggle-fav/', views.api_vault_toggle_fav, name='api_vault_toggle_fav'),
    path('api/vault/delete/', views.api_vault_delete, name='api_vault_delete'),
]
