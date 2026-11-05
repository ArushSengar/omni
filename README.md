# OmniRoute AI Gateway & Hermes Agent Infrastructure

> A unified, resilient, multi-provider AI gateway and autonomous agent system deployed on ARM64 Raspberry Pi 4, featuring persistent public Cloudflare Tunnel exposure and cryptographically managed OmniKeys.

---

## 🌟 Architecture Overview

```mermaid
graph TD
    Client[Remote Clients / Apps / Scripts] -->|HTTPS / Bearer OmniKey| CF[Cloudflare Edge Tunnel]
    LocalClient[Local LAN / Dev Machines] -->|HTTP / Bearer OmniKey| Pi
    CF -->|QUIC / HTTP/2| Pi[Raspberry Pi 4 192.168.0.100]
    
    subgraph Pi Host
        TunnelSvc[omniroute-tunnel.service]
        OmniSvc[omniroute.service :20128]
        HermesAgent[Hermes Agent CLI & Dashboard]
        OmniDB[(storage.sqlite)]
        
        TunnelSvc -.->|Proxy| OmniSvc
        HermesAgent -->|hermes-brain Combo| OmniSvc
        OmniSvc <--> OmniDB
    end
    
    subgraph Upstream Providers (1,070+ Models)
        OmniSvc --> Google[Google Antigravity Pro]
        OmniSvc --> Mistral[Codestral / Mistral AI]
        OmniSvc --> Cerebras[Cerebras Fast Inference]
        OmniSvc --> Groq[Groq Llama 3]
        OmniSvc --> Kimi[Moonshot Kimi]
    end
```

---

## 🚀 Key Features

1. **Multi-Provider Unified Routing**:
   - OpenAI-compatible `/v1/chat/completions` and `/v1/models` endpoints.
   - 1,070+ models accessible through a single host.
   - Automated fallback chains (`hermes-brain`, `hermes-fast`).

2. **Secure Public Internet Access**:
   - Zero-trust HTTPS tunnel via Cloudflare Edge (`*.trycloudflare.com`).
   - Managed automatically by systemd (`omniroute-tunnel.service`).
   - URL auto-discovery written to `~/.omniroute/public_url.txt`.

3. **OmniKeys Client Authentication**:
   - Strict Bearer token authentication (`REQUIRE_API_KEY=true`).
   - Constant-time SHA-256 validation.
   - Comprehensive CLI management (`omnikey list`, `create`, `rotate`, `revoke`, `test`).
   - Per-key budget limits, quota caps, and model permission whitelists.

4. **Hermes Autonomous Agent**:
   - Hermes Agent updated to `v0.22.7 (2026.9.24)`.
   - Browser automation powered by ARM64 Chromium 1248 (Chrome 156 for Testing).
   - Direct integration via `custom:omni` provider pointing to `hermes-brain`.

---

## 📁 Repository Structure

```text
omni/
├── config/
│   ├── omniroute.env.production      # Production environment configuration for Pi
│   ├── omniroute-tunnel.service      # Systemd service unit for Cloudflare Tunnel
│   ├── hermes_config.yaml.example    # Hermes Agent configuration template
│   └── provider_topology.json        # Connected provider topology snapshot
├── scripts/
│   ├── omni_keys_manager.py          # OmniKey management tool (cross-platform CLI)
│   ├── launch_tunnel.sh              # Tunnel runner with live URL extraction
│   ├── get_public_url.py             # Fetch current active public URL from Pi
│   ├── test_remote_api.py            # End-to-end HTTPS verification script
│   ├── setup_pi_omniroute.sh         # One-shot installation & deployment script
│   └── verify_all_providers.py       # Upstream connection diagnostic tool
├── OMNIKEYS_GUIDE.md                 # OmniKey management and client integration guide
├── OMNIROUTE_TIPS_TRICKS.md          # SBC performance tuning, compression, caching
└── README.md                         # Master documentation (this file)
```

---

## ⚡ Quick Start

### 1. Check OmniKeys & Service Status on the Pi
```bash
# SSH into Raspberry Pi
ssh arush@192.168.0.100

# List configured OmniKeys
omnikey list

# Check services
systemctl status omniroute
systemctl status omniroute-tunnel
```

### 2. Retrieve Public Tunnel URL
From your local computer:
```bash
python scripts/get_public_url.py
```
*Example Output:*
```text
Current OmniRoute Public URL: https://copy-genetics-overhead-backed.trycloudflare.com
OpenAI Base URL: https://copy-genetics-overhead-backed.trycloudflare.com/v1
```

### 3. Verify Remote Access
```bash
python scripts/test_remote_api.py
```
*Output:*
```text
Testing OmniRoute Public API at https://copy-genetics-overhead-backed.trycloudflare.com...
[SUCCESS] /v1/models responded with HTTP 200 - Total Models: 1074
[SUCCESS] /v1/chat/completions responded with HTTP 200!
Model: gemini-3.8-flash-high
Assistant Response: OmniRoute Public API is fully operational!
```

---

## 🔑 Managing OmniKeys

Use the `omnikey` CLI on the Pi or `python scripts/omni_keys_manager.py`:

```bash
# Create a new key with unlimited access
omnikey create "work-laptop"

# Create a key with a $10.00 daily budget cap
omnikey create "contractor-key" --daily-limit 10.0

# Rotate an existing key
omnikey rotate "work-laptop"

# Revoke a key
omnikey revoke "contractor-key"
```

For client integration code samples (Python OpenAI SDK, LangChain, cURL, Claude Code), see [`OMNIKEYS_GUIDE.md`](./OMNIKEYS_GUIDE.md).

---

## 🛠️ Performance Tuning & Best Practices

For memory caps (`OMNIROUTE_MEMORY_MB`), startup timeouts, token compression workers, and cache TTL tuning, read [`OMNIROUTE_TIPS_TRICKS.md`](./OMNIROUTE_TIPS_TRICKS.md).
