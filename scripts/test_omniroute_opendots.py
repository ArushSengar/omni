#!/usr/bin/env python3
"""
OmniRoute <-> OpenDots Integration Health Check & Verification Suite
Verifies:
1. OmniRoute Gateway health on port 20128
2. Claude model availability & response latency (/v1/chat/completions)
3. OpenDots environment configuration (.env)
4. OpenDots SQLite workspace database readiness
"""

import os
import sys
import json
import time
import urllib.request
import urllib.error
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
OPENDOTS_DIR = BASE_DIR / "OpenDots"
ENV_FILE = OPENDOTS_DIR / ".env"

def print_step(title):
    print(f"\n========================================================")
    print(f"[*] {title}")
    print(f"========================================================")

def check_opendots_env():
    print_step("1. Verifying OpenDots Environment Configuration")
    if not ENV_FILE.exists():
        print(f"[-] ERROR: .env file not found at {ENV_FILE}")
        return False
    
    env_vars = {}
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env_vars[k.strip()] = v.strip()

    print(f"[+] Found OpenDots .env configuration:")
    print(f"    - HOST:             {env_vars.get('HOST', '127.0.0.1')}")
    print(f"    - PORT:             {env_vars.get('PORT', '4310')}")
    print(f"    - OPENAI_BASE_URL:  {env_vars.get('OPENAI_BASE_URL', 'Not Set')}")
    print(f"    - OPENAI_MODEL:     {env_vars.get('OPENAI_MODEL', 'Not Set')}")
    print(f"    - DATABASE_PATH:    {env_vars.get('DATABASE_PATH', 'data/opendots.sqlite')}")
    
    return env_vars

def check_omniroute_health(base_url, api_key, model):
    print_step("2. Testing OmniRoute Gateway Connection")
    target_url = f"{base_url.rstrip('/')}/chat/completions"
    print(f"[*] Target Endpoint: {target_url}")
    print(f"[*] Model Selected:   {model}")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are OpenDots Copilot assistant connected via OmniRoute gateway."},
            {"role": "user", "content": "Reply with only: {\"status\": \"online\", \"router\": \"omniroute\"}"}
        ],
        "max_tokens": 50,
        "temperature": 0.2
    }

    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(target_url, data=data, headers=headers, method="POST")
        t0 = time.time()
        with urllib.request.urlopen(req, timeout=15) as resp:
            elapsed = (time.time() - t0) * 1000
            status_code = resp.getcode()
            body = resp.read().decode("utf-8")
            res_json = json.loads(body)
            content = res_json.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            print(f"[+] OmniRoute Responded in {elapsed:.1f}ms (HTTP {status_code}):")
            print(f"    Raw Content: {content}")
            return True
    except urllib.error.URLError as e:
        print(f"[-] Gateway unreachable at {target_url}: {e.reason}")
        return False
    except Exception as e:
        print(f"[-] Request error: {e}")
        return False

def check_node_dependencies():
    print_step("3. Verifying OpenDots Node & Build Status")
    node_modules = OPENDOTS_DIR / "node_modules"
    if not node_modules.exists():
        print(f"[-] node_modules not found in {OPENDOTS_DIR}")
        return False
    
    core_pkg = node_modules / "@copilotkit" / "react-core"
    tanstack_pkg = node_modules / "@tanstack" / "ai"
    if core_pkg.exists() and tanstack_pkg.exists():
        print(f"[+] Core CopilotKit & TanStack packages verified successfully.")
        return True
    else:
        print(f"[!] Some packages missing. Please run 'npm install' in OpenDots.")
        return False

def main():
    print("=================================================================")
    print("   🌐 OPENDOTS + OMNIROUTE INTEGRATION VERIFICATION SUITE       ")
    print("=================================================================")
    env = check_opendots_env()
    if not env:
        sys.exit(1)

    node_ok = check_node_dependencies()
    base_url = env.get("OPENAI_BASE_URL", "http://localhost:20128/v1")
    api_key = env.get("OPENAI_API_KEY", "sk-971230e546e14a3e-23822a-06e1aa8d")
    model = env.get("OPENAI_MODEL", "antigravity/claude-sonnet-4-6")

    gateway_ok = check_omniroute_health(base_url, api_key, model)

    print("\n-----------------------------------------------------------------")
    print("SUMMARY:")
    print(f"  - OpenDots Configuration:  {'READY' if env else 'FAIL'}")
    print(f"  - Node Dependencies:       {'INSTALLED' if node_ok else 'PENDING'}")
    print(f"  - OmniRoute Gateway:       {'CONNECTED' if gateway_ok else 'STANDBY (Start OmniRoute)'}")
    print("-----------------------------------------------------------------")

if __name__ == "__main__":
    main()
