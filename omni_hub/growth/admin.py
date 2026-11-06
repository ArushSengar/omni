from django.contrib import admin
from .models import GrowthPost, ResearchTopic, SystemStatus, WeeklyGrowthReview

@admin.register(GrowthPost)
class GrowthPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'domain', 'status', 'likes', 'views', 'comments', 'created_at')
    list_filter = ('status', 'domain', 'source')
    search_fields = ('title', 'linkedin_content', 'twitter_content')

@admin.register(ResearchTopic)
class ResearchTopicAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'is_used', 'researched_at')
    list_filter = ('category', 'is_used')
    search_fields = ('title', 'technical_problem', 'solution')

@admin.register(SystemStatus)
class SystemStatusAdmin(admin.ModelAdmin):
    list_display = ('pi_uptime', 'pi_ram_free', 'omniroute_status', 'last_sync')

@admin.register(WeeklyGrowthReview)
class WeeklyGrowthReviewAdmin(admin.ModelAdmin):
    list_display = ('period_label', 'growth_status', 'avg_views', 'engagement_rate', 'created_at')
    list_filter = ('growth_status',)
