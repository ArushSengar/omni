from django.contrib import admin
from .models import GrowthPost, ResearchTopic, SystemStatus

@admin.register(GrowthPost)
class GrowthPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'domain', 'status', 'created_at', 'likes', 'views')
    list_filter = ('status', 'domain', 'source')
    search_fields = ('title', 'linkedin_content', 'twitter_content')
    date_hierarchy = 'created_at'

@admin.register(ResearchTopic)
class ResearchTopicAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'is_used', 'researched_at')
    list_filter = ('is_used', 'category')
    search_fields = ('title', 'technical_problem', 'solution')

@admin.register(SystemStatus)
class SystemStatusAdmin(admin.ModelAdmin):
    list_display = ('omniroute_status', 'pi_ram_free', 'last_sync')
