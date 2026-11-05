---
name: omniroute-admin
description: Administer OmniRoute gateway, inspect public Cloudflare tunnel, and manage OmniKeys.
version: 1.0.0
---

# OmniRoute Administrator Skill

This skill allows Hermes to inspect, manage, and troubleshoot the OmniRoute AI Gateway, Cloudflare public tunnel, and client OmniKeys.

## Architecture Quick Reference
- **Local Gateway Port**: `20128` (Service: `omniroute.service`)
- **Public Tunnel Service**: `omniroute-tunnel.service` (Cloudflare Quick Tunnel)
- **Active Public URL**: stored in `/home/arush/.omniroute/public_url.txt`
- **Config**: `/home/arush/.omniroute/.env` (Security: `REQUIRE_API_KEY=true`)
- **Database**: `/home/arush/.omniroute/storage.sqlite`
- **Combos**: `hermes-brain` (primary reasoning), `hermes-fast` (background crons)

## Key Commands

### 1. Check Gateway & Tunnel Health
```bash
# Check service states
systemctl status omniroute --no-pager
systemctl status omniroute-tunnel --no-pager

# Get active public tunnel URL
cat /home/arush/.omniroute/public_url.txt

# Test local gateway health
curl -s -H "Authorization: Bearer sk-971230e546e14a3e-23822a-06e1aa8d" http://127.0.0.1:20128/v1/models | head -n 10
```

### 2. Manage OmniKeys
OmniRoute uses `/usr/local/bin/omnikey` for key management:
```bash
# List all keys
omnikey list

# Create a new key for a client or subagent
omnikey create "client-name"

# Create a budget-capped key ($5/day)
omnikey create "budget-agent" --daily-limit 5.0

# Rotate an existing key
omnikey rotate "client-name"

# Revoke a key
omnikey revoke "client-name"

# Test key against the local server
omnikey test "<key_secret>"
```

### 3. Restart / Self-Heal
If OmniRoute or the tunnel goes down:
```bash
# Restart gateway
sudo systemctl restart omniroute

# Restart tunnel
sudo systemctl restart omniroute-tunnel
```
