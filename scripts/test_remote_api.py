import urllib.request
import json
import sys

URL = "https://copy-genetics-overhead-backed.trycloudflare.com"
API_KEY = "sk-omni-89b46b201df1ad14ee40da0f2ed964ba-64a2c6d7"

print(f"Testing OmniRoute Public API at {URL}...")

# 1. Test /v1/models
models_url = f"{URL}/v1/models"
req = urllib.request.Request(models_url, headers={
    "Authorization": f"Bearer {API_KEY}",
    "User-Agent": "OmniClient/1.0"
})

try:
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        model_count = len(data.get("data", []))
        print(f"[SUCCESS] /v1/models responded with HTTP {resp.status} - Total Models: {model_count}")
except Exception as e:
    print(f"[FAILED] /v1/models error: {e}")
    sys.exit(1)

# 2. Test /v1/chat/completions
chat_url = f"{URL}/v1/chat/completions"
payload = json.dumps({
    "model": "antigravity/gemini-3.8-flash-high",
    "messages": [
        {"role": "user", "content": "You are connected via a public Cloudflare tunnel to OmniRoute on Raspberry Pi 4. Reply with exactly: 'OmniRoute Public API is fully operational!'"}
    ]
}).encode('utf-8')

req2 = urllib.request.Request(chat_url, data=payload, headers={
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "User-Agent": "OmniClient/1.0"
})

try:
    with urllib.request.urlopen(req2, timeout=25) as resp:
        res = json.loads(resp.read().decode('utf-8'))
        content = res["choices"][0]["message"]["content"]
        tokens = res.get("usage", {})
        print(f"[SUCCESS] /v1/chat/completions responded with HTTP {resp.status}!")
        print(f"Model: {res.get('model')}")
        print(f"Assistant Response:\n{content}")
        print(f"Token Usage: {tokens}")
except Exception as e:
    print(f"[FAILED] /v1/chat/completions error: {e}")
    sys.exit(1)

