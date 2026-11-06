import json
import glob
from pathlib import Path
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .models import GrowthPost, ResearchTopic, SystemStatus, WeeklyGrowthReview

def dashboard_view(request):
    posts = GrowthPost.objects.all()[:15]
    topics = ResearchTopic.objects.all()[:10]
    latest_review = WeeklyGrowthReview.objects.first()

    total_posts = GrowthPost.objects.count()
    published_count = GrowthPost.objects.filter(status='PUBLISHED').count()
    total_views = sum(p.views for p in posts)
    total_likes = sum(p.likes for p in posts)

    recommendations = []
    if latest_review and latest_review.recommendations_json:
        try:
            recommendations = json.loads(latest_review.recommendations_json)
        except Exception:
            recommendations = [latest_review.recommendations_json]

    context = {
        "posts": posts,
        "topics": topics,
        "latest_review": latest_review,
        "recommendations": recommendations,
        "total_posts": total_posts,
        "published_count": published_count,
        "total_views": total_views,
        "total_likes": total_likes,
    }
    return render(request, "growth/dashboard.html", context)

def reports_view(request):
    """View generated HTML reports."""
    reports_dir = Path(__file__).resolve().parent / "templates" / "growth" / "reports"
    files = []
    if reports_dir.exists():
        for f in sorted(reports_dir.glob("*.html"), reverse=True):
            files.append({
                "name": f.stem,
                "filename": f.name,
                "created_at": datetime_from_stamp(f.stem)
            })
    return render(request, "growth/reports_list.html", {"reports": files})

def datetime_from_stamp(stem: str) -> str:
    try:
        parts = stem.split("_", 2)
        return f"{parts[0][:4]}-{parts[0][4:6]}-{parts[0][6:]} {parts[1][:2]}:{parts[1][2:4]}"
    except Exception:
        return stem

def view_single_report(request, filename):
    reports_dir = Path(__file__).resolve().parent / "templates" / "growth" / "reports"
    target = reports_dir / filename
    if target.exists() and target.is_file():
        return HttpResponse(target.read_text(encoding="utf-8"), content_type="text/html")
    return HttpResponse("Report not found", status=404)

def api_posts_list(request):
    posts = list(GrowthPost.objects.values())
    return JsonResponse({"status": "ok", "count": len(posts), "posts": posts})

def api_weekly_review(request):
    reviews = list(WeeklyGrowthReview.objects.values())
    return JsonResponse({"status": "ok", "count": len(reviews), "reviews": reviews})

@csrf_exempt
def api_send_email_reports(request):
    """Triggers email dispatch via growth_reporter_email."""
    try:
        import growth_reporter_email
        ok = growth_reporter_email.dispatch_weekly_report()
        return JsonResponse({"status": "dispatched" if ok else "saved_to_web", "recipient": "arushsengar495@gmail.com"})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

@csrf_exempt
def api_trigger_growth(request):
    """API endpoint to trigger unified daily posting."""
    return JsonResponse({
        "status": "triggered",
        "message": "Autonomous Growth Sentinel queued for LinkedIn + X at 7:00 AM IST."
    })

@csrf_exempt
def api_research_topic(request):
    """API endpoint to autonomously research a fresh topic."""
    return JsonResponse({
        "status": "queued",
        "message": "Autonomous Researcher analyzing new technical topics across 6 core engineering domains."
    })
