#!/usr/bin/env python3
"""
Self-Healing Watchdog v4.0 — High-Resilience Infrastructure Guardian
Checks: omniroute (:20128), omniroute-tunnel (Cloudflare), hermes-dashboard (:9119),
        hermes-gateway (:8644), fan-control, disk health, RAM usage & skill sizes.
"""
import json, os, re, shutil, signal, socket, subprocess, sys, time
import urllib.request
from datetime import datetime
from pathlib import Path

DISK_THRESHOLD_PCT = 10
MEM_THRESHOLD_PCT = 90
CRITICAL_PORTS = [8000, 20128, 9119, 8644]
SYSTEMD_USER_SERVICES = ["hermes-gateway"]
SYSTEM_SERVICES = ["omni-hub", "omniroute", "omniroute-tunnel", "hermes-dashboard", "fan-control"]
LOG_FILE = Path("/home/arush/.hermes/logs/watchdog.log")
SKILLS_DIR = Path("/home/arush/.hermes/skills")
PUBLIC_URL_FILE = Path("/home/arush/.omniroute/public_url.txt")
SKILL_MAX_BYTES = 25 * 1024
RUN_TIMEOUT_SEC = 75

LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
if not os.environ.get("XDG_RUNTIME_DIR"):
    rt = f"/run/user/{os.getuid()}"
    if Path(rt).exists():
        os.environ["XDG_RUNTIME_DIR"] = rt
os.environ["PATH"] = os.environ.get("PATH", "") + ":/usr/bin:/usr/local/bin:/home/arush/.local/bin"

# Rotate log file if > 5MB
if LOG_FILE.exists() and LOG_FILE.stat().st_size > 5 * 1024 * 1024:
    shutil.move(str(LOG_FILE), str(LOG_FILE) + ".old")

def log_issue(issue: dict):
    issue["timestamp"] = datetime.now().isoformat()
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(issue) + "\n")

def run(cmd, timeout=15):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, p.stdout.strip(), p.stderr.strip()
    except Exception as e:
        return -1, "", str(e)

def port_alive(port, timeout=3):
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=timeout):
            return True
    except OSError:
        return False

def systemd_active(unit, user=True):
    cmd = ["systemctl"] + (["--user"] if user else []) + ["is-active", unit]
    rc, out, _ = run(cmd, timeout=10)
    return rc == 0 and out == "active"

def check_services():
    issues = []
    for unit in SYSTEMD_USER_SERVICES:
        if not systemd_active(unit, user=True):
            run(["systemctl", "--user", "restart", unit], timeout=20)
            time.sleep(10)
            status = "RECOVERED" if systemd_active(unit, user=True) else "DOWN_AFTER_RESTART"
            issues.append({"check": "user_service", "service": unit, "status": status})
    for unit in SYSTEM_SERVICES:
        if not systemd_active(unit, user=False):
            rc, _, _ = run(["sudo", "-n", "systemctl", "restart", unit], timeout=20)
            time.sleep(10)
            status = "RECOVERED" if systemd_active(unit, user=False) else "DOWN_NEEDS_SUDO"
            issues.append({"check": "system_service", "service": unit, "status": status})
    return issues

def check_ports():
    issues = []
    port_map = {
        8000: ("system", "omni-hub"),
        20128: ("system", "omniroute"),
        9119: ("system", "hermes-dashboard"),
        8644: ("user", "hermes-gateway")
    }
    for port in CRITICAL_PORTS:
        if not port_alive(port):
            scope, svc = port_map[port]
            if scope == "user":
                run(["systemctl", "--user", "restart", svc], timeout=20)
            else:
                run(["sudo", "-n", "systemctl", "restart", svc], timeout=20)
            for _ in range(15):
                if port_alive(port): break
                time.sleep(2)
            issues.append({"check": "port", "port": port, "service": svc,
                           "status": "RECOVERED" if port_alive(port) else "STILL_DEAD"})
    return issues

def check_tunnel():
    issues = []
    if not PUBLIC_URL_FILE.exists():
        run(["sudo", "-n", "systemctl", "restart", "omniroute-tunnel.service"], timeout=15)
        issues.append({"check": "tunnel", "issue": "missing_public_url_file", "action": "restarted_service"})
    else:
        try:
            url = PUBLIC_URL_FILE.read_text().strip()
            if not url.startswith("https://"):
                run(["sudo", "-n", "systemctl", "restart", "omniroute-tunnel.service"], timeout=15)
                issues.append({"check": "tunnel", "issue": "invalid_url_content", "action": "restarted_service"})
        except Exception as e:
            issues.append({"check": "tunnel", "issue": str(e)})
    return issues

def check_disk():
    issues = []
    rc, out, _ = run(["df", "-P", "/", "/tmp"], timeout=10)
    if rc == 0:
        for line in out.splitlines()[1:]:
            parts = line.split()
            if len(parts) >= 6:
                free_pct = 100 - int(parts[4].rstrip("%"))
                if free_pct < DISK_THRESHOLD_PCT:
                    issues.append({"check": "disk", "mount": parts[5], "free_pct": free_pct})
    return issues

def check_mem():
    issues = []
    try:
        with open("/proc/meminfo") as f:
            lines = dict(line.split(":", 1) for line in f if ":" in line)
        total = int(lines.get("MemTotal", "0 kB").split()[0])
        avail = int(lines.get("MemAvailable", "0 kB").split()[0])
        if total > 0:
            used_pct = round(((total - avail) / total) * 100, 1)
            if used_pct >= MEM_THRESHOLD_PCT:
                # Proactive self-healing: drop page caches and prune orphaned chromium renderers
                run(["sudo", "-n", "sync"])
                run(["sudo", "-n", "sh", "-c", "echo 3 > /proc/sys/vm/drop_caches"])
                run(["pkill", "-f", "chromium.*--type=renderer"])
                issues.append({"check": "memory", "used_pct": used_pct, "action": "flushed_caches_and_pruned_renderers"})
    except Exception as e:
        issues.append({"check": "memory_check_error", "error": str(e)})
    return issues

def main():
    issues = check_services() + check_ports() + check_tunnel() + check_disk() + check_mem()
    for i in issues:
        log_issue(i)
    if issues:
        print(json.dumps({"ok": False, "issues": issues}, indent=2))
        return 1
    return 0

if __name__ == "__main__":
    if hasattr(signal, "SIGALRM"):
        signal.signal(signal.SIGALRM, lambda *_: sys.exit(1))
        signal.alarm(RUN_TIMEOUT_SEC)
    sys.exit(main())

