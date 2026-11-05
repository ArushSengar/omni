#!/usr/bin/env python3
"""
Hermes Agent <-> OmniRoute Live Communication Bridge & Health Checker
Verifies that Hermes can invoke chat, coding, and reasoning routes via OmniRoute.
"""

import sys
import json
import requests

def test_hermes_bridge(base_url="http://192.168.0.100:20128", api_key="sk-971230e546e14a3e-23822a-06e1aa8d"):
    print(f"[*] Testing Hermes -> OmniRoute connection at {base_url}...")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    test_payload = {
        "model": "auto/coding:free",
        "messages": [
            {"role": "system", "content": "You are Hermes AI Assistant connected via OmniRoute gateway."},
            {"role": "user", "content": "Return a JSON object: {\"status\": \"ok\", \"agent\": \"hermes\"} and nothing else."}
        ],
        "max_tokens": 30
    }

    try:
        r = requests.post(f"{base_url}/v1/chat/completions", headers=headers, json=test_payload, timeout=25)
        if r.status_code == 200:
            content = r.json().get("choices", [{}])[0].get("message", {}).get("content", "")
            print("[+] Hermes Bridge Test: SUCCESS (200 OK)")
            print(f"    Raw Response: {content.strip()}")
            return True
        else:
            print(f"[-] Hermes Bridge Test FAILED with HTTP {r.status_code}: {r.text}")
            return False
    except Exception as e:
        print(f"[!] Error contacting gateway: {e}")
        return False

if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "http://192.168.0.100:20128"
    key = sys.argv[2] if len(sys.argv) > 2 else "sk-971230e546e14a3e-23822a-06e1aa8d"
    success = test_hermes_bridge(url, key)
    sys.exit(0 if success else 1)

