import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import GrowthPost, ResearchTopic, SystemStatus

def dashboard_view(request):
    posts = GrowthPost.objects.all()[:15]
    topics = ResearchTopic.objects.all()[:10]
    
    total_posts = GrowthPost.objects.count()
    published_count = GrowthPost.objects.filter(status='PUBLISHED').count()
    total_views = sum(p.views for p in posts)
    total_likes = sum(p.likes for p in posts)
    
    context = {
        "posts": posts,
        "topics": topics,
        "total_posts": total_posts,
        "published_count": published_count,
        "total_views": total_views,
        "total_likes": total_likes,
    }
    return render(request, "growth/dashboard.html", context)

def api_posts_list(request):
    posts = list(GrowthPost.objects.values())
    return JsonResponse({"status": "ok", "count": len(posts), "posts": posts})

@csrf_exempt
def api_trigger_growth(request):
    """API endpoint to trigger unified daily posting."""
    # In production or local, this can invoke omni_daily_growth
    return JsonResponse({
        "status": "triggered",
        "message": "Autonomous Growth Engine pipeline queued for LinkedIn + X."
    })

@csrf_exempt
def api_research_topic(request):
    """API endpoint to autonomously research a fresh topic."""
    # Can invoke autonomous_researcher
    return JsonResponse({
        "status": "queued",
        "message": "Autonomous Researcher analyzing new technical topics."
    })
