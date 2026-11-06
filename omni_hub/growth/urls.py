from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('api/posts/', views.api_posts_list, name='api_posts'),
    path('api/weekly-review/', views.api_weekly_review, name='api_weekly_review'),
    path('api/trigger-growth/', views.api_trigger_growth, name='api_trigger_growth'),
    path('api/research-topic/', views.api_research_topic, name='api_research_topic'),
]
