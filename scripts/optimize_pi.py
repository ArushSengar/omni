import subprocess
import sys
from pathlib import Path

PLINK_BASE = [
    "plink", "-batch",
    "-hostkey", "SHA256:Spg7rum7lHwouvgx6d2YtcxYMK0xr5e2pmTDQBfGARU",
    "-pw", "arush",
    "arush@192.168.0.100"
]

def run_remote(cmd, input_data=None):
    if input_data:
        p = subprocess.run(PLINK_BASE + [cmd], input=input_data, capture_output=True)
    else:
        p = subprocess.run(PLINK_BASE + [cmd], capture_output=True, text=True)
    return p.returncode, p.stdout if isinstance(p.stdout, str) else p.stdout.decode('utf-8', 'replace'), p.stderr if isinstance(p.stderr, str) else p.stderr.decode('utf-8', 'replace')

print("=== 1. Configuring Kernel Sysctl Parameters (/etc/sysctl.d/99-omni-pi.conf) ===")
sysctl_conf = """# Omni Homelab Pi 4 High-Performance Kernel Parameters
vm.swappiness = 15
vm.vfs_cache_pressure = 50
vm.dirty_background_ratio = 5
vm.dirty_ratio = 10
net.core.somaxconn = 4096
net.ipv4.tcp_max_syn_backlog = 4096
net.ipv4.tcp_fin_timeout = 15
fs.file-max = 2097152
"""
code, out, err = run_remote("sudo tee /etc/sysctl.d/99-omni-pi.conf > /dev/null && sudo sysctl -p /etc/sysctl.d/99-omni-pi.conf", input_data=sysctl_conf.encode('utf-8'))
print("Sysctl Result:\n", out.strip())
if err:
    print("Sysctl Stderr:", err.strip())

print("\n=== 2. Configuring Systemd Journal Limits (/etc/systemd/journald.conf.d/00-journal-size.conf) ===")
journal_conf = """[Journal]
SystemMaxUse=50M
SystemMaxFileSize=10M
MaxRetentionSec=1month
"""
code, out, err = run_remote("sudo mkdir -p /etc/systemd/journald.conf.d && sudo tee /etc/systemd/journald.conf.d/00-journal-size.conf > /dev/null && sudo systemctl restart systemd-journald", input_data=journal_conf.encode('utf-8'))
print("Journald tuned to 50M limit. Exit code:", code)

print("\n=== 3. Optimizing Systemd Services (LimitNOFILE=65536) ===")
omni_hub_service = """[Unit]
Description=Omni Master Hub Command Center
After=network.target

[Service]
Type=simple
User=arush
WorkingDirectory=/home/arush/omni_hub
ExecStart=/usr/bin/python3 manage.py runserver 0.0.0.0:8000
Restart=always
RestartSec=3
LimitNOFILE=65536
Environment=PYTHONUNBUFFERED=1
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
"""
code, out, err = run_remote("sudo tee /etc/systemd/system/omni-hub.service > /dev/null && sudo systemctl daemon-reload && sudo systemctl restart omni-hub.service", input_data=omni_hub_service.encode('utf-8'))
print("omni-hub.service updated with LimitNOFILE=65536 and restarted. Code:", code)

print("\n=== 4. Deploying hermes_omnivault.py Bridge to Pi ===")
local_script = Path("hermes/scripts/hermes_omnivault.py").read_bytes()
code, out, err = run_remote("cat > /home/arush/hermes_omnivault.py && chmod +x /home/arush/hermes_omnivault.py && sudo ln -sf /home/arush/hermes_omnivault.py /usr/local/bin/hermes-omnivault && mkdir -p /home/arush/.local/bin && ln -sf /home/arush/hermes_omnivault.py /home/arush/.local/bin/hermes-omnivault", input_data=local_script)
print("hermes_omnivault.py deployed and symlinked to /usr/local/bin/hermes-omnivault. Code:", code)

print("\n=== 5. Deploying omnivault-memory Skill to Hermes ===")
local_skill = Path("hermes/skills/omnivault-memory/SKILL.md").read_bytes()
code, out, err = run_remote("mkdir -p /home/arush/.hermes/skills/omnivault-memory && cat > /home/arush/.hermes/skills/omnivault-memory/SKILL.md", input_data=local_skill)
print("omnivault-memory skill installed in /home/arush/.hermes/skills/omnivault-memory/. Code:", code)

print("\n=== 6. Updating Hermes SOUL.md with OmniVault Directive ===")
soul_directive = """

### 10. OMNIVAULT & OMNI HUB MULTIMODAL MEMORY INTEGRATION:
- OmniVault on Port 8000 (`http://192.168.0.100:8000/vault/`) is your external multimodal tool memory and resource library.
- Whenever Arush provides an image, screenshot, website trick, tool, or document:
  1. DO NOT tell Arush to open the web browser or manually upload it.
  2. You autonomously ingest and save it using `hermes-omnivault ingest-image "<path>"` or `python3 /home/arush/hermes_omnivault.py ingest-image "<path>"`.
  3. Extract OCR, parse technical features, auto-categorize it, generate a punchy 1-line usage description ("Use case: ..."), and save it directly into the OmniVault database.
  4. Present the saved result immediately: Title, Category, and the 1-line purpose description.
- When Arush provides a URL or trick: run `hermes-omnivault ingest-url "<url>"` or `hermes-omnivault ingest-note "<text>"`.
- When Arush asks "Maine iske liye kaunsa tool save kiya tha?" or "OSINT tools dikhao", query `hermes-omnivault search "<topic>"` to retrieve and answer him instantly.
- You can query `hermes-omnivault wallet` anytime to check live AI provider quotas and dollar savings across all 11 providers.
- You can query `hermes-omnivault status` to check Pi 4 thermal readings and RAM utilization.
"""
code, out, err = run_remote("grep -q 'OMNIVAULT & OMNI HUB' /home/arush/.hermes/SOUL.md || tee -a /home/arush/.hermes/SOUL.md > /dev/null", input_data=soul_directive.encode('utf-8'))
print("Hermes SOUL.md updated with OmniVault directive. Code:", code)

print("\n=== 7. Appending God-Mode v5.0 Memory Log to Hermes MEMORY.md ===")
memory_log = """

§
God-Mode v5.0 Complete Omni Hub & OmniVault Autonomous Architecture (November 10, 2026):
- MASTER COCKPIT: http://192.168.0.100:8000/ (Apple iOS 18 Glassmorphism Command Center).
- OMNIVAULT MULTIMODAL REPOSITORY: http://192.168.0.100:8000/vault/
  * Dual Ingest Support: Web UI (Screenshot OCR, URL crawl, PDF extract, Quick Note) + Direct Hermes CLI (`hermes-omnivault`).
  * Automatic Categorization: 7 domains (AI & Prompts, Web Tricks, Cyber Security/OSINT, Dev APIs, Media, Homelab, Research).
  * 1-Line Punchy Purpose: Automatically generated for every saved resource so Arush instantly understands what it does.
  * Legality Triage: SAFE, PENTEST_ONLY, CAUTION, SUSPICIOUS flags with security notes.
  * Interactive Favorites: Clickable star button with instant AJAX toggle and persistent counts.
- AI PROVIDER WALLET & QUOTAS:
  * 11 Live Model Providers: GitHub Copilot, Cloudflare AI, Google AI Studio, Codestral, Cohere, Groq, Amazon Q, Kiro, Veo, AI Horde, DuckDuckGo.
  * 4 Cascading Combo Tiers: code, chat, fast, cheap with automatic fallback routing.
  * Real-Time Token & Dollar Savings Counter.
- SECURITY & LAN ACCESS GUARD:
  * Full password protection across all views and APIs via OmniAuthMiddleware.
  * Apple iOS 18 Glassmorphic Lock Screen (`/login/`).
  * Passcode mode (`arush@omni2026` or `arush`) + Credentials mode (`arush`/`arush`) with 30-day session security.
- MOBILE & PHONE OPTIMIZATION:
  * Apple iOS 18 Bottom Tab Bar (Cockpit, Vault, Services, Clean, Copilot, Tabs).
  * Full touch-first responsive design, zero horizontal scroll, and safe-area padding.
- HERMES UNIVERSAL BRIDGE:
  * Tool: `hermes-omnivault [ingest-image|ingest-url|ingest-note|search|wallet|status]`
  * Skill: `omnivault-memory` (`~/.hermes/skills/omnivault-memory/SKILL.md`)
  * Autonomously saves any screenshot or trick Arush mentions without requiring manual web upload.
"""
code, out, err = run_remote("grep -q 'God-Mode v5.0' /home/arush/.hermes/memories/MEMORY.md || tee -a /home/arush/.hermes/memories/MEMORY.md > /dev/null", input_data=memory_log.encode('utf-8'))
print("Hermes MEMORY.md updated with God-Mode v5.0 specs. Code:", code)

print("\n=== 8. Creating Dedicated Daily Memory File for Hermes ===")
code, out, err = run_remote("tee /home/arush/.hermes/memories/2026-11-10_omnihub_omnivault_upgrade.md > /dev/null", input_data=memory_log.encode('utf-8'))
print("Created /home/arush/.hermes/memories/2026-11-10_omnihub_omnivault_upgrade.md. Code:", code)

print("\n=== System Optimization & Integration Complete! ===")

