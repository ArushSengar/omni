#!/usr/bin/env python3
"""
OmniRoute End-to-End Comprehensive Provider Verification Suite
Usage: python verify_all_providers.py [--host http://192.168.0.100:20128] [--key <API_KEY>]
"""

import sys
import time
import argparse
import requests

DEFAULT_BASE_URL = "http://192.168.0.100:20128"
DEFAULT_HERMES_KEY = "sk-971230e546e14a3e-23822a-06e1aa8d"

TARGET_MODELS = [
    # Category, Display Name, Model ID
    ("Smart Combo", "Hermes Free Coding", "auto/coding:free"),
    ("Smart Combo", "Best Coding Engine", "auto/best-coding"),
    ("Smart Combo", "Best Chat Engine", "auto/best-chat"),
    ("Smart Combo", "Best Reasoning Engine", "auto/best-reasoning"),
    ("Direct Model", "GitHub Copilot GPT-4o", "github/gpt-4o"),
    ("Direct Model", "DuckDuckGo GPT-4o Mini", "duckduckgo-web/gpt-4o-mini"),
    ("Direct Model", "DuckDuckGo Claude 3", "duckduckgo-web/claude-3-haiku"),
    ("Direct Model", "Google Antigravity Gemini 3", "antigravity/gemini-3-flash"),
    ("Direct Model", "Mistral Codestral", "codestral/codestral-latest"),
    ("Direct Model", "Cohere Command R+", "cohere/command-r-plus-08-2024"),
    ("Direct Model", "Groq LPU Accelerator", "groq/openai/gpt-oss-120b"),
    ("Direct Model", "Cloudflare Llama 3.3 70B", "cloudflare-playground/@cf/meta/llama-3.3-70b-instruct-fp8-fast"),
]

def check_health(base_url):
    print(f"[*] Checking Gateway Health at {base_url}/api/health ...")
    try:
        r = requests.get(f"{base_url}/api/health", timeout=5)
        if r.status_code == 200:
            print("    [+] OmniRoute Gateway: ONLINE (200 OK)")
            return True
        else:
            print(f"    [-] OmniRoute Gateway responded with HTTP {r.status_code}")
            return False
    except Exception as e:
        print(f"    [!] Failed to connect to OmniRoute Gateway: {e}")
        return False

def test_model(base_url, api_key, model_id, prompt="Reply with 'ONLINE' and nothing else."):
    url = f"{base_url}/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model_id,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 15
    }
    t0 = time.time()
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=30)
        latency_ms = int((time.time() - t0) * 1000)
        if r.status_code == 200:
            data = r.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            content_clean = content.replace("\n", " ").strip()
            return True, f"{latency_ms}ms", content_clean[:35]
        else:
            err = r.json().get("error", {}).get("message", r.text[:40]) if "application/json" in r.headers.get("Content-Type", "") else r.text[:40]
            return False, f"{latency_ms}ms", f"HTTP {r.status_code}: {err[:30]}"
    except Exception as e:
        return False, "TIMEOUT", str(e)[:35]

def main():
    parser = argparse.ArgumentParser(description="OmniRoute Verification Suite")
    parser.add_argument("--host", default=DEFAULT_BASE_URL, help="OmniRoute Base URL")
    parser.add_argument("--key", default=DEFAULT_HERMES_KEY, help="OmniRoute API Key")
    args = parser.parse_args()

    if not check_health(args.host):
        print("\n[!] Exiting because gateway is unreachable.")
        sys.exit(1)

    print("\n" + "=" * 90)
    print(f"{'Category':<14} {'Service / Name':<28} {'Status':<10} {'Latency':<10} {'Response / Message'}")
    print("=" * 90)

    passed = 0
    total = len(TARGET_MODELS)

    for cat, name, model_id in TARGET_MODELS:
        ok, latency, msg = test_model(args.host, args.key, model_id)
        status_str = "PASS" if ok else "FAIL"
        if ok:
            passed += 1
        print(f"{cat:<14} {name:<28} {status_str:<10} {latency:<10} {msg}")

    print("=" * 90)
    print(f"\n[+] Verification Complete: {passed}/{total} services passing successfully.")
    if passed >= 8:
        print("[+] System Status: EXCELLENT — Ready for Hermes and production AI workloads.")
    else:
        print("[-] System Status: PARTIAL — Some endpoints require credential updates.")

if __name__ == "__main__":
    main()

