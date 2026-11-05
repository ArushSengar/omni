# OmniKeys Management & Remote Client Integration Guide

OmniKeys provide high-entropy, cryptographically secured Bearer tokens (`sk-omni-...`) to control client access to OmniRoute's 1,000+ AI models and automated fallback combos.

---

## 1. OmniKey Architecture

Every OmniKey is structured as follows:
- **Secret Key Token**: High-entropy string formatted as `sk-omni-<32-hex-bytes>-<8-hex-bytes>`.
- **Validation**: OmniRoute validates incoming requests using a constant-time SHA-256 fingerprint hash (`key_hash`). The raw secret is never stored in plaintext in the operational hot path.
- **Access Control**:
  - `model_access_mode`: `'all'` (access to all 1070+ models) or `'restricted'` (whitelisted models only).
  - `allowed_combos`: Patterns such as `["combo/*"]` for full fallback chain usage.
  - `usage_limit_enabled` & `daily_usage_limit_usd`: Soft or hard daily dollar spending caps.
  - `compression_enabled`: Token compression support for tool-calling agent loops.

---

## 2. Using the `omnikey` CLI (On Raspberry Pi)

The Raspberry Pi has `omnikey` pre-installed globally (`/usr/local/bin/omnikey`).

### List Active Keys
```bash
omnikey list
```
*Output:*
```text
==============================================================================================================
ID                                     NAME                     PREFIX         ACTIVE   ACCESS   DAILY LIMIT  CREATED
==============================================================================================================
c71c2fbd-ae1e-4fc0-add7-1c39f4a93f73   remote-client-primary    sk-omni-89b4   YES      all      Unlimited    2026-11-05
8658e710-adee-49ee-ba0e-edac475c2034   hermes                   sk-971230e54   YES      all      Unlimited    2026-09-10
==============================================================================================================
```

### Generate a New Key
```bash
# Full access key
omnikey create "laptop-claude-code"

# Key with daily spending limit of $5.00
omnikey create "dev-team-member" --daily-limit 5.0

# Key restricted to specific models
omnikey create "curated-agent" --models "antigravity/gemini-3.8-flash-high" "codestral/codestral-2508"
```

### Rotate a Compromised or Old Key
```bash
omnikey rotate "remote-client-primary"
# Or by ID:
omnikey rotate "c71c2fbd-ae1e-4fc0-add7-1c39f4a93f73"
```

### Revoke a Key
```bash
omnikey revoke "laptop-claude-code"
```

### Test a Key
```bash
omnikey test "sk-omni-89b46b201df1ad14ee40da0f2ed964ba-64a2c6d7"
```

---

## 3. Remote Client Integration Examples

### A. Python (Official OpenAI SDK)
```python
from openai import OpenAI

# Use either the public Cloudflare tunnel or your local LAN IP
client = OpenAI(
    base_url="https://<your-tunnel-subdomain>.trycloudflare.com/v1",
    api_key="sk-omni-89b46b201df1ad14ee40da0f2ed964ba-64a2c6d7"
)

response = client.chat.completions.create(
    model="hermes-brain",  # Or "antigravity/gemini-3.8-flash-high", "codestral/codestral-2508"
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Explain quantum computing in one sentence."}
    ]
)

print(response.choices[0].message.content)
```

### B. cURL (Command Line)
```bash
curl -X POST "https://<your-tunnel-subdomain>.trycloudflare.com/v1/chat/completions" \
  -H "Authorization: Bearer sk-omni-89b46b201df1ad14ee40da0f2ed964ba-64a2c6d7" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "antigravity/gemini-3.8-flash-high",
    "messages": [
      {"role": "user", "content": "Hello via public Cloudflare tunnel!"}
    ]
  }'
```

### C. LangChain / LangGraph
```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="antigravity/claude-sonnet-4-6",
    openai_api_base="https://<your-tunnel-subdomain>.trycloudflare.com/v1",
    openai_api_key="sk-omni-89b46b201df1ad14ee40da0f2ed964ba-64a2c6d7"
)

print(llm.invoke("What is the speed of light?").content)
```

### D. Claude Code CLI
```bash
export ANTHROPIC_BASE_URL="https://<your-tunnel-subdomain>.trycloudflare.com/v1"
export ANTHROPIC_API_KEY="sk-omni-89b46b201df1ad14ee40da0f2ed964ba-64a2c6d7"
claude
```

