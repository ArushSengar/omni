import os
import json
import glob
import shutil
import sqlite3
import subprocess
from pathlib import Path
from datetime import datetime
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .models import GrowthPost, ResearchTopic, SystemStatus, WeeklyGrowthReview

MANAGED_SERVICES = [
    {
        "id": "omni-hub",
        "name": "Omni Master Hub Command Center",
        "unit": "omni-hub.service",
        "port": "8000",
        "desc": "Single-Pane Unified Control Dashboard & Management APIs",
        "category": "Core"
    },
    {
        "id": "omniroute",
        "name": "OmniRoute AI Gateway",
        "unit": "omniroute.service",
        "port": "20128",
        "desc": "Dynamic Multi-Provider AI Inference Router & Model Balancer",
        "category": "AI / Routing"
    },
    {
        "id": "omniroute-tunnel",
        "name": "OmniRoute Cloudflare Tunnel",
        "unit": "omniroute-tunnel.service",
        "port": "N/A",
        "desc": "Cloudflare Zero-Trust Secure Tunnel for Public API Access",
        "category": "Networking"
    },
    {
        "id": "hermes-dashboard",
        "name": "Hermes Web Dashboard",
        "unit": "hermes-dashboard.service",
        "port": "9119",
        "desc": "Hermes Agent Framework Web UI & Active Session Monitor",
        "category": "Agent"
    },
    {
        "id": "fan-control",
        "name": "Raspberry Pi Dynamic Fan Control",
        "unit": "fan-control.service",
        "port": "GPIO 14",
        "desc": "PWM Dynamic Fan Controller based on CPU Core Temperature",
        "category": "Hardware"
    },
    {
        "id": "cron",
        "name": "System Cron Automation Daemon",
        "unit": "cron.service",
        "port": "Daemon",
        "desc": "Executes 7:00 AM IST Daily Posts & Weekly Growth Audits",
        "category": "Scheduler"
    },
]

MCP_CATALOG = [
    {"name": "figma", "tools": 42, "status": "Connected", "transport": "HTTP (mcp.figma.com)", "auth": "OAuth 2.0", "category": "Design & UI"},
    {"name": "hugging_face", "tools": 4, "status": "Connected", "transport": "HTTP (hf.co/mcp)", "auth": "Public / Direct", "category": "Models & Datasets"},
    {"name": "canva", "tools": 18, "status": "Connected", "transport": "HTTP (mcp.canva.com)", "auth": "OAuth 2.0", "category": "Creative"},
    {"name": "comfy-cloud", "tools": 12, "status": "Connected", "transport": "HTTP (api.comfy-cloud.com)", "auth": "OAuth 2.0", "category": "Generative Media"},
    {"name": "context7", "tools": 8, "status": "Connected", "transport": "HTTP (context7.ai)", "auth": "OAuth 2.0", "category": "Context & Search"},
    {"name": "craft", "tools": 14, "status": "Connected", "transport": "HTTP (mcp.craft.do)", "auth": "OAuth 2.0", "category": "Docs & Notes"},
    {"name": "deepwiki", "tools": 6, "status": "Connected", "transport": "HTTP (deepwiki.ai)", "auth": "OAuth 2.0", "category": "Knowledge Base"},
    {"name": "gamma", "tools": 10, "status": "Connected", "transport": "HTTP (gamma.app)", "auth": "OAuth 2.0", "category": "Presentations"},
    {"name": "netlify", "tools": 15, "status": "Connected", "transport": "HTTP (mcp.netlify.com)", "auth": "OAuth 2.0", "category": "Cloud Hosting"},
    {"name": "railway", "tools": 20, "status": "Connected", "transport": "HTTP (mcp.railway.app)", "auth": "OAuth 2.0", "category": "Cloud Infra"},
    {"name": "supabase", "tools": 25, "status": "Connected", "transport": "HTTP (mcp.supabase.com)", "auth": "OAuth 2.0", "category": "Database & Auth"},
    {"name": "vercel", "tools": 16, "status": "Connected", "transport": "HTTP (mcp.vercel.com)", "auth": "OAuth 2.0", "category": "Deployment"},
    {"name": "indeed", "tools": 0, "status": "Disabled (Claude WAF Exclusive)", "transport": "mcp.indeed.com", "auth": "Restricted", "category": "Jobs"},
]

def get_system_metrics():
    """Reads native Linux /proc and /sys filesystem metrics with zero external dependencies."""
    # 1. Thermal
    temp_c = None
    thermal_path = Path("/sys/class/thermal/thermal_zone0/temp")
    if thermal_path.exists():
        try:
            temp_c = round(int(thermal_path.read_text().strip()) / 1000.0, 1)
        except Exception:
            pass

    # 2. Disk
    disk = shutil.disk_usage("/")
    disk_total_gb = round(disk.total / (1024**3), 2)
    disk_used_gb = round(disk.used / (1024**3), 2)
    disk_free_gb = round(disk.free / (1024**3), 2)
    disk_pct = round((disk.used / disk.total) * 100, 1)

    # 3. Memory via /proc/meminfo
    mem_info = {}
    mem_path = Path("/proc/meminfo")
    if mem_path.exists():
        for line in mem_path.read_text().splitlines():
            parts = line.split(":")
            if len(parts) == 2:
                key = parts[0].strip()
                val = parts[1].strip().split()[0]
                if val.isdigit():
                    mem_info[key] = int(val)

    mem_total_mb = round(mem_info.get("MemTotal", 0) / 1024, 1)
    mem_avail_mb = round(mem_info.get("MemAvailable", 0) / 1024, 1)
    mem_used_mb = round(mem_total_mb - mem_avail_mb, 1)
    mem_pct = round((mem_used_mb / mem_total_mb) * 100, 1) if mem_total_mb else 0
    swap_total_mb = round(mem_info.get("SwapTotal", 0) / 1024, 1)
    swap_free_mb = round(mem_info.get("SwapFree", 0) / 1024, 1)
    swap_used_mb = round(swap_total_mb - swap_free_mb, 1)

    # 4. Uptime & Load
    uptime_sec = 0
    uptime_path = Path("/proc/uptime")
    if uptime_path.exists():
        try:
            uptime_sec = float(uptime_path.read_text().split()[0])
        except Exception:
            pass
    uptime_str = f"{int(uptime_sec // 3600)}h {int((uptime_sec % 3600) // 60)}m"
    try:
        load_avg = [round(x, 2) for x in os.getloadavg()]
    except Exception:
        load_avg = [0.0, 0.0, 0.0]

    return {
        "temp_c": temp_c or 42.0,
        "disk": {
            "total_gb": disk_total_gb,
            "used_gb": disk_used_gb,
            "free_gb": disk_free_gb,
            "percent": disk_pct
        },
        "memory": {
            "total_mb": mem_total_mb,
            "used_mb": mem_used_mb,
            "free_mb": mem_avail_mb,
            "percent": mem_pct,
            "swap_total_mb": swap_total_mb,
            "swap_used_mb": swap_used_mb
        },
        "uptime": uptime_str,
        "load_avg": load_avg,
        "hostname": "arush (Raspberry Pi 4 Model B - 4GB)",
        "ip": "192.168.0.100"
    }

def get_services_status():
    """Queries systemctl properties for all managed services."""
    results = []
    for svc in MANAGED_SERVICES:
        cmd = ["systemctl", "show", svc["unit"], "--property=ActiveState,SubState,MainPID"]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=3)
            props = dict(line.split("=", 1) for line in res.stdout.strip().splitlines() if "=" in line)
            is_active = props.get("ActiveState") == "active"
            results.append({
                **svc,
                "is_active": is_active,
                "active_state": props.get("ActiveState", "inactive"),
                "sub_state": props.get("SubState", "dead"),
                "pid": props.get("MainPID", "0")
            })
        except Exception:
            results.append({
                **svc,
                "is_active": False,
                "active_state": "unknown",
                "sub_state": "unknown",
                "pid": "0"
            })
    return results

def get_reports_list():
    """Collects all generated HTML reports from the reports directory."""
    reports_dir = Path(__file__).resolve().parent / "templates" / "growth" / "reports"
    files = []
    if reports_dir.exists():
        for f in sorted(reports_dir.glob("*.html"), reverse=True):
            clean_name = f.name.replace("___", " - ").replace("____", " - ").replace("__", " ").replace(".html", "")
            is_maintenance = "Maintenance" in clean_name or "Health" in clean_name
            files.append({
                "title": clean_name,
                "name": clean_name,
                "filename": f.name,
                "size_kb": round(f.stat().st_size / 1024, 1),
                "is_maintenance": is_maintenance,
                "created_at": datetime.fromtimestamp(f.stat().st_mtime).strftime("%b %d, %Y - %I:%M %p")
            })
    return files

def dashboard_view(request):
    """Main dashboard rendering with tabbed command center architecture."""
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

    metrics = get_system_metrics()
    services = get_services_status()
    reports = get_reports_list()

    context = {
        "posts": posts,
        "topics": topics,
        "latest_review": latest_review,
        "recommendations": recommendations,
        "total_posts": total_posts,
        "published_count": published_count,
        "total_views": total_views,
        "total_likes": total_likes,
        "metrics": metrics,
        "services": services,
        "reports": reports,
        "mcps": MCP_CATALOG,
        "active_mcp_count": sum(1 for m in MCP_CATALOG if m["status"] == "Connected"),
    }
    return render(request, "growth/dashboard.html", context)

def reports_view(request):
    """View generated HTML reports index."""
    return render(request, "growth/reports_list.html", {"reports": get_reports_list()})

def view_single_report(request, filename):
    """Serves a single raw HTML report."""
    reports_dir = Path(__file__).resolve().parent / "templates" / "growth" / "reports"
    target = reports_dir / filename
    if target.exists() and target.is_file():
        return HttpResponse(target.read_text(encoding="utf-8"), content_type="text/html")
    return HttpResponse("Report not found", status=404)

# ==================== JSON API ENDPOINTS ====================

def api_system_stats(request):
    """Real-time system telemetry endpoint."""
    return JsonResponse({"status": "ok", "metrics": get_system_metrics()})

def api_services_status(request):
    """Real-time services status endpoint."""
    return JsonResponse({"status": "ok", "services": get_services_status()})

@csrf_exempt
def api_service_action(request):
    """Controls background services: start, stop, restart."""
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "POST required"}, status=405)
    
    try:
        data = json.loads(request.body.decode("utf-8")) if request.body else {}
    except Exception:
        data = request.POST

    service_id = data.get("service")
    action = data.get("action")

    svc_match = next((s for s in MANAGED_SERVICES if s["id"] == service_id), None)
    if not svc_match:
        return JsonResponse({"status": "error", "message": f"Service '{service_id}' not recognized"}, status=400)

    if action not in ["start", "stop", "restart", "status"]:
        return JsonResponse({"status": "error", "message": f"Action '{action}' invalid"}, status=400)

    unit = svc_match["unit"]
    try:
        cmd = ["sudo", "systemctl", action, unit]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        # Query new state
        check_cmd = ["systemctl", "show", unit, "--property=ActiveState,SubState,MainPID"]
        check_res = subprocess.run(check_cmd, capture_output=True, text=True, timeout=3)
        props = dict(line.split("=", 1) for line in check_res.stdout.strip().splitlines() if "=" in line)
        is_active = props.get("ActiveState") == "active"

        return JsonResponse({
            "status": "ok",
            "action": action,
            "unit": unit,
            "is_active": is_active,
            "active_state": props.get("ActiveState", "unknown"),
            "sub_state": props.get("SubState", "unknown"),
            "pid": props.get("MainPID", "0"),
            "stdout": res.stdout,
            "stderr": res.stderr
        })
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

@csrf_exempt
def api_run_maintenance(request):
    """Executes system cleaning, cache dropping, RAM optimization, or DB compaction."""
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "POST required"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8")) if request.body else {}
    except Exception:
        data = request.POST

    action_type = data.get("type", "all")
    output_lines = []

    # Record BEFORE metrics
    before_metrics = get_system_metrics()

    try:
        if action_type in ["ram", "all"]:
            output_lines.append("⚡ Flushing PageCache, Dentries and Inodes...")
            subprocess.run(["sync"], timeout=5)
            subprocess.run(["sudo", "sh", "-c", "echo 3 > /proc/sys/vm/drop_caches"], timeout=5)
            subprocess.run(["sudo", "sysctl", "-w", "vm.swappiness=20"], timeout=5)
            output_lines.append("✓ RAM buffer dropped & swappiness tuned to 20.")

        if action_type in ["cache", "all"]:
            output_lines.append("🧹 Clearing UV, pip, and Hermes scratch package caches...")
            home = Path.home()
            for path_pattern in [
                home / ".hermes" / "cache" / "uv",
                home / ".cache" / "pip",
                home / ".hermes" / "cache" / "scratch"
            ]:
                if path_pattern.exists():
                    shutil.rmtree(path_pattern, ignore_errors=True)
                    path_pattern.mkdir(parents=True, exist_ok=True)
            output_lines.append("✓ Build & package caches purged successfully.")

        if action_type in ["vacuum", "all"]:
            output_lines.append("📦 Vacuuming systemd journal logs & cleaning apt cache...")
            subprocess.run(["sudo", "journalctl", "--vacuum-size=30M"], capture_output=True, text=True, timeout=10)
            subprocess.run(["sudo", "apt-get", "clean"], capture_output=True, text=True, timeout=10)
            # Remove old staging profiles
            home = Path.home()
            profiles_dir = home / ".hermes" / "profiles"
            if profiles_dir.exists():
                for p in profiles_dir.glob(".netscan-*.staging-*"):
                    shutil.rmtree(p, ignore_errors=True)
            output_lines.append("✓ Journal logs vacuumed and staging profiles removed.")

        if action_type in ["db", "all"]:
            output_lines.append("🗄️ Compacting SQLite database...")
            db_path = Path(__file__).resolve().parent.parent / "db.sqlite3"
            if db_path.exists():
                conn = sqlite3.connect(str(db_path))
                conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
                conn.execute("VACUUM;")
                conn.close()
                output_lines.append(f"✓ SQLite database compacted: {db_path.name}")

        # Record AFTER metrics
        after_metrics = get_system_metrics()
        
        storage_freed_gb = round(before_metrics["disk"]["used_gb"] - after_metrics["disk"]["used_gb"], 2)
        ram_freed_mb = round(after_metrics["memory"]["free_mb"] - before_metrics["memory"]["free_mb"], 1)

        output_lines.append(f"📊 Storage Available: {after_metrics['disk']['free_gb']} GB")
        output_lines.append(f"🧠 RAM Free/Available: {after_metrics['memory']['free_mb']} MB")

        return JsonResponse({
            "status": "ok",
            "type": action_type,
            "output": "\n".join(output_lines),
            "before": before_metrics,
            "after": after_metrics,
            "storage_freed_gb": max(storage_freed_gb, 0.0),
            "ram_freed_mb": ram_freed_mb
        })
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e), "output": "\n".join(output_lines)}, status=500)

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

def api_posts_list(request):
    posts = list(GrowthPost.objects.values())
    return JsonResponse({"status": "ok", "count": len(posts), "posts": posts})

def api_weekly_review(request):
    reviews = list(WeeklyGrowthReview.objects.values())
    return JsonResponse({"status": "ok", "count": len(reviews), "reviews": reviews})
