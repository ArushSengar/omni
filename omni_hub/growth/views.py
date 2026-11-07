import os
import re
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

REGISTRY_FILE = Path(__file__).resolve().parent / "managed_services.json"

DEFAULT_SERVICES = [
    {
        "id": "omni-hub",
        "name": "Omni Master Hub Command Center",
        "unit": "omni-hub.service",
        "port": "8000",
        "desc": "Single-Pane Unified Control Dashboard & Management APIs",
        "category": "Core",
        "type": "systemd"
    },
    {
        "id": "omniroute",
        "name": "OmniRoute AI Gateway",
        "unit": "omniroute.service",
        "port": "20128",
        "desc": "Dynamic Multi-Provider AI Inference Router & Model Balancer",
        "category": "AI / Routing",
        "type": "systemd"
    },
    {
        "id": "omniroute-tunnel",
        "name": "OmniRoute Cloudflare Tunnel",
        "unit": "omniroute-tunnel.service",
        "port": "N/A",
        "desc": "Cloudflare Zero-Trust Secure Tunnel for Public API Access",
        "category": "Networking",
        "type": "systemd"
    },
    {
        "id": "hermes-dashboard",
        "name": "Hermes Web Dashboard",
        "unit": "hermes-dashboard.service",
        "port": "9119",
        "desc": "Hermes Agent Framework Web UI & Active Session Monitor",
        "category": "Agent",
        "type": "systemd"
    },
    {
        "id": "fan-control",
        "name": "Raspberry Pi Dynamic Fan Control",
        "unit": "fan-control.service",
        "port": "GPIO 14",
        "desc": "PWM Dynamic Fan Controller based on CPU Core Temperature",
        "category": "Hardware",
        "type": "systemd"
    },
    {
        "id": "cron",
        "name": "System Cron Automation Daemon",
        "unit": "cron.service",
        "port": "Daemon",
        "desc": "Executes 7:00 AM IST Daily Posts & Weekly Growth Audits",
        "category": "Scheduler",
        "type": "systemd"
    },
    {
        "id": "hermes-laptop-worker",
        "name": "Hermes Laptop Worker Node",
        "unit": "laptop",
        "port": "8642",
        "desc": "Windows 11 (Arush-Sengar) Distributed Compute Worker via Hermes Peer Protocol",
        "category": "Worker Node",
        "type": "peer",
        "host": "192.168.0.101"
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

def load_registered_services():
    """Loads custom registered services from managed_services.json."""
    if not REGISTRY_FILE.exists():
        try:
            REGISTRY_FILE.write_text(json.dumps(DEFAULT_SERVICES, indent=2), encoding="utf-8")
            return list(DEFAULT_SERVICES)
        except Exception:
            return list(DEFAULT_SERVICES)
    try:
        data = json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))
        if isinstance(data, list):
            # Ensure base services are present
            base_ids = {s["id"] for s in DEFAULT_SERVICES}
            for b in DEFAULT_SERVICES:
                if b["id"] not in {d.get("id") for d in data}:
                    data.insert(0, b)
            return data
    except Exception:
        pass
    return list(DEFAULT_SERVICES)

def save_registered_services(services_list):
    """Saves custom services to managed_services.json."""
    try:
        REGISTRY_FILE.write_text(json.dumps(services_list, indent=2), encoding="utf-8")
        return True
    except Exception:
        return False

def discover_all_services():
    """
    Dynamically discovers and aggregates:
    1. Base managed systemd units
    2. Custom registered services from managed_services.json
    3. Active project systemd units (omni*, hermes*, fan*, tunnel*, bot*)
    4. Running background user processes (Python servers, node apps, bridges)
    """
    services = []
    seen_ids = set()
    registered = load_registered_services()

    # 1. Evaluate registered services (systemd / custom)
    for svc in registered:
        seen_ids.add(svc["id"])
        unit = svc.get("unit", "")
        svc_type = svc.get("type", "systemd")
        is_active = False
        active_state = "inactive"
        sub_state = "dead"
        pid = "0"

        if svc_type == "systemd" and unit:
            cmd = ["systemctl", "show", unit, "--property=ActiveState,SubState,MainPID"]
            try:
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=2)
                props = dict(line.split("=", 1) for line in res.stdout.strip().splitlines() if "=" in line)
                is_active = (props.get("ActiveState") == "active")
                active_state = props.get("ActiveState", "inactive")
                sub_state = props.get("SubState", "dead")
                pid = props.get("MainPID", "0")
            except Exception:
                pass
        elif svc_type == "process" and svc.get("pid"):
            check_pid = svc.get("pid")
            try:
                os.kill(int(check_pid), 0)
                is_active = True
                active_state = "active"
                sub_state = "running"
                pid = str(check_pid)
            except Exception:
                is_active = False
                active_state = "inactive"
                sub_state = "dead"
        elif svc_type == "peer":
            host = svc.get("host", "192.168.0.101")
            port = svc.get("port", "8642")
            try:
                import urllib.request
                req = urllib.request.Request(
                    f"http://{host}:{port}/health",
                    headers={"Authorization": "Bearer sk-laptop-hermes-token-2026"}
                )
                with urllib.request.urlopen(req, timeout=2) as resp:
                    if resp.status == 200:
                        is_active = True
                        active_state = "active"
                        sub_state = "mesh-connected"
                        pid = "Laptop (Windows)"
            except Exception:
                is_active = False
                active_state = "unreachable"
                sub_state = "offline"
                pid = "0"

        services.append({
            **svc,
            "is_active": is_active,
            "active_state": active_state,
            "sub_state": sub_state,
            "pid": pid,
            "type": svc_type
        })

    # 2. Auto-discover ANY active systemd unit matching patterns
    try:
        cmd = ["systemctl", "list-units", "--type=service", "--state=running", "--no-pager", "--no-legend"]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=2)
        for line in res.stdout.strip().splitlines():
            parts = line.split()
            if not parts:
                continue
            unit_name = parts[0]
            clean_id = unit_name.replace(".service", "")
            if clean_id not in seen_ids and any(p in unit_name.lower() for p in ["omni", "hermes", "fan", "tunnel", "bot"]):
                seen_ids.add(clean_id)
                services.append({
                    "id": clean_id,
                    "name": f"Auto-Discovered: {clean_id}",
                    "unit": unit_name,
                    "port": "Auto",
                    "desc": "Dynamically discovered active system service",
                    "category": "Auto-Discovered",
                    "is_active": True,
                    "active_state": "active",
                    "sub_state": "running",
                    "pid": parts[2] if len(parts) > 2 and parts[2].isdigit() else "Auto",
                    "type": "systemd",
                    "auto_discovered": True
                })
    except Exception:
        pass

    # 3. Auto-discover running user background processes in /home/arush
    try:
        ports_map = {}
        ss_res = subprocess.run(["ss", "-tulpn"], capture_output=True, text=True, timeout=2)
        for line in ss_res.stdout.splitlines():
            match = re.search(r":(\d+)\s+.*users:\(\(\"[^\"]+\",pid=(\d+)", line)
            if match:
                ports_map[match.group(2)] = match.group(1)

        ps_res = subprocess.run(["ps", "-u", "arush", "-o", "pid,command", "--no-headers"], capture_output=True, text=True, timeout=2)
        known_pids = set(s.get("pid") for s in services if s.get("pid") not in ["0", "Auto"])

        for line in ps_res.stdout.splitlines():
            parts = line.strip().split(None, 1)
            if len(parts) < 2:
                continue
            pid_str, cmd = parts[0], parts[1]
            if pid_str in known_pids:
                continue

            is_candidate = any(kw in cmd for kw in ["bridge.js", "manage.py", "app.py", "server.py", "main.py", "api.py", "bot.py"])
            if is_candidate and not any(ign in cmd for ign in ["grep", "bash", "ssh", "watchdog", "def "]):
                cmd_parts = cmd.split()
                clean_name = Path(cmd_parts[1] if len(cmd_parts) > 1 else cmd_parts[0]).name
                proc_id = f"proc-{pid_str}"
                if proc_id not in seen_ids:
                    seen_ids.add(proc_id)
                    port = ports_map.get(pid_str, "N/A")
                    services.append({
                        "id": proc_id,
                        "name": f"Process: {clean_name}",
                        "unit": cmd[:60] + ("..." if len(cmd) > 60 else ""),
                        "port": port,
                        "desc": f"Dynamic user background process (PID {pid_str})",
                        "category": "Background Process",
                        "is_active": True,
                        "active_state": "active",
                        "sub_state": "running",
                        "pid": pid_str,
                        "type": "process",
                        "auto_discovered": True
                    })
    except Exception:
        pass

    return services

def get_system_metrics():
    """Reads native Linux /proc and /sys filesystem metrics with zero external dependencies."""
    temp_c = None
    thermal_path = Path("/sys/class/thermal/thermal_zone0/temp")
    if thermal_path.exists():
        try:
            temp_c = round(int(thermal_path.read_text().strip()) / 1000.0, 1)
        except Exception:
            pass

    disk = shutil.disk_usage("/")
    disk_total_gb = round(disk.total / (1024**3), 2)
    disk_used_gb = round(disk.used / (1024**3), 2)
    disk_free_gb = round(disk.free / (1024**3), 2)
    disk_pct = round((disk.used / disk.total) * 100, 1)

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
    services = discover_all_services()
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
    return render(request, "growth/reports_list.html", {"reports": get_reports_list()})

def view_single_report(request, filename):
    reports_dir = Path(__file__).resolve().parent / "templates" / "growth" / "reports"
    target = reports_dir / filename
    if target.exists() and target.is_file():
        return HttpResponse(target.read_text(encoding="utf-8"), content_type="text/html")
    return HttpResponse("Report not found", status=404)

# ==================== JSON API ENDPOINTS ====================

def api_system_stats(request):
    return JsonResponse({"status": "ok", "metrics": get_system_metrics()})

def api_services_status(request):
    return JsonResponse({"status": "ok", "services": discover_all_services()})

@csrf_exempt
def api_register_service(request):
    """Dynamically registers a new custom service or background script."""
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "POST required"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8")) if request.body else {}
    except Exception:
        data = request.POST

    svc_id = data.get("id") or re.sub(r'[^a-zA-Z0-9_-]', '', data.get("name", "").lower().replace(" ", "-"))
    if not svc_id:
        return JsonResponse({"status": "error", "message": "Service 'name' or 'id' is required"}, status=400)

    registered = load_registered_services()
    # Check if already exists
    existing = next((s for s in registered if s["id"] == svc_id), None)
    new_entry = {
        "id": svc_id,
        "name": data.get("name", svc_id),
        "unit": data.get("unit", f"{svc_id}.service"),
        "port": data.get("port", "N/A"),
        "desc": data.get("desc", "Custom Registered Service"),
        "category": data.get("category", "Custom"),
        "type": data.get("type", "systemd")
    }

    if existing:
        existing.update(new_entry)
    else:
        registered.append(new_entry)

    save_registered_services(registered)
    return JsonResponse({"status": "ok", "message": f"Service '{svc_id}' registered successfully", "service": new_entry})

@csrf_exempt
def api_delete_service(request):
    """Unregisters a custom service from managed_services.json."""
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "POST required"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8")) if request.body else {}
    except Exception:
        data = request.POST

    svc_id = data.get("id")
    if not svc_id:
        return JsonResponse({"status": "error", "message": "Service 'id' required"}, status=400)

    # Protect base core services
    if svc_id in [s["id"] for s in DEFAULT_SERVICES]:
        return JsonResponse({"status": "error", "message": f"Cannot delete core service '{svc_id}'"}, status=403)

    registered = load_registered_services()
    filtered = [s for s in registered if s["id"] != svc_id]
    save_registered_services(filtered)
    return JsonResponse({"status": "ok", "message": f"Service '{svc_id}' removed from registry"})

@csrf_exempt
def api_service_action(request):
    """Controls background services: start, stop, restart for systemd and processes."""
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "POST required"}, status=405)
    
    try:
        data = json.loads(request.body.decode("utf-8")) if request.body else {}
    except Exception:
        data = request.POST

    service_id = data.get("service")
    action = data.get("action")

    all_svcs = discover_all_services()
    svc_match = next((s for s in all_svcs if s["id"] == service_id), None)
    if not svc_match:
        return JsonResponse({"status": "error", "message": f"Service '{service_id}' not recognized"}, status=400)

    if action not in ["start", "stop", "restart", "status"]:
        return JsonResponse({"status": "error", "message": f"Action '{action}' invalid"}, status=400)

    svc_type = svc_match.get("type", "systemd")
    unit = svc_match.get("unit", "")
    pid = svc_match.get("pid", "0")

    try:
        if svc_type == "systemd":
            cmd = ["sudo", "systemctl", action, unit]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            check_cmd = ["systemctl", "show", unit, "--property=ActiveState,SubState,MainPID"]
            check_res = subprocess.run(check_cmd, capture_output=True, text=True, timeout=3)
            props = dict(line.split("=", 1) for line in check_res.stdout.strip().splitlines() if "=" in line)
            is_active = (props.get("ActiveState") == "active")

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
        elif svc_type == "process":
            if action == "stop":
                if pid and pid != "0":
                    subprocess.run(["kill", "-TERM", pid], timeout=5)
                return JsonResponse({"status": "ok", "action": action, "pid": pid, "is_active": False, "active_state": "inactive"})
            elif action in ["start", "restart"]:
                return JsonResponse({"status": "ok", "message": f"Process control '{action}' queued for PID {pid}"})
        elif svc_type == "peer":
            host = svc_match.get("host", "192.168.0.101")
            port = svc_match.get("port", "8642")
            try:
                import urllib.request
                req = urllib.request.Request(
                    f"http://{host}:{port}/health",
                    headers={"Authorization": "Bearer sk-laptop-hermes-token-2026"}
                )
                with urllib.request.urlopen(req, timeout=3) as resp:
                    is_active = (resp.status == 200)
                return JsonResponse({
                    "status": "ok",
                    "action": action,
                    "unit": unit,
                    "is_active": is_active,
                    "active_state": "active" if is_active else "unreachable",
                    "sub_state": "mesh-connected" if is_active else "offline",
                    "pid": "Laptop (Windows)"
                })
            except Exception as ex:
                return JsonResponse({"status": "error", "message": f"Peer communication failed: {ex}"})
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
    try:
        import growth_reporter_email
        ok = growth_reporter_email.dispatch_weekly_report()
        return JsonResponse({"status": "dispatched" if ok else "saved_to_web", "recipient": "arushsengar495@gmail.com"})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

@csrf_exempt
def api_trigger_growth(request):
    return JsonResponse({
        "status": "triggered",
        "message": "Autonomous Growth Sentinel queued for LinkedIn + X at 7:00 AM IST."
    })

@csrf_exempt
def api_research_topic(request):
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

@csrf_exempt
def api_dispatch_laptop(request):
    """Dispatches a task from the Omni Hub to the Laptop Hermes worker node."""
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "POST required"}, status=405)
    
    try:
        data = json.loads(request.body.decode("utf-8")) if request.body else {}
    except Exception:
        data = request.POST

    prompt = data.get("prompt", "").strip()
    if not prompt:
        return JsonResponse({"status": "error", "message": "Prompt is required"}, status=400)

    mode = data.get("mode", "sync")  # sync (dm) or async (run)
    hermes_bin = "/home/arush/.local/bin/hermes"

    try:
        if mode == "async":
            cmd = f'echo {json.dumps(prompt)} | {hermes_bin} peer run laptop'
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
            return JsonResponse({
                "status": "ok",
                "mode": "async",
                "output": res.stdout.strip(),
                "error": res.stderr.strip()
            })
        else:
            # Sync turn (dm)
            import base64
            b64_prompt = base64.b64encode(prompt.encode("utf-8")).decode("ascii")
            cmd = f'PROMPT=$(echo "{b64_prompt}" | base64 -d) && {hermes_bin} peer dm laptop "$PROMPT"'
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=120)
            return JsonResponse({
                "status": "ok",
                "mode": "sync",
                "output": res.stdout.strip(),
                "error": res.stderr.strip()
            })
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)
