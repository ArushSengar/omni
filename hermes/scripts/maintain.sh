#!/usr/bin/env bash
# ==============================================================================
# Autonomous Maintenance & Self-Healing Suite v4.0 (Raspberry Pi 4 ARM64)
# ==============================================================================
set -e

export PATH="$HOME/.local/bin:$HOME/.cargo/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

LOG_FILE="/home/arush/maintain.log"
echo "=== [$(date)] Starting Autonomous Pi Maintenance ===" | tee "$LOG_FILE"

# 1. Package & Security Upgrades
echo "--- [1/7] Updating Debian Packages & Security Patches ---" | tee -a "$LOG_FILE"
sudo apt-get update -y && sudo apt-get --only-upgrade install -y libssl3 openssl curl ca-certificates || true
sudo apt-get autoremove -y && sudo apt-get clean -y

# 2. Verify OmniRoute & Tunnel
echo "--- [2/7] Verifying OmniRoute & Public Cloudflare Tunnel ---" | tee -a "$LOG_FILE"
sudo systemctl is-active --quiet omniroute || sudo systemctl restart omniroute
sudo systemctl is-active --quiet omniroute-tunnel || sudo systemctl restart omniroute-tunnel

if [ -f /home/arush/.omniroute/public_url.txt ]; then
    PUBLIC_URL=$(cat /home/arush/.omniroute/public_url.txt)
    echo "Active Public Tunnel URL: $PUBLIC_URL" | tee -a "$LOG_FILE"
else
    echo "Warning: Public URL file not found, restarting tunnel..." | tee -a "$LOG_FILE"
    sudo systemctl restart omniroute-tunnel
fi

# 3. Verify OmniKeys & Local API
echo "--- [3/7] Verifying OmniKey Authentication ---" | tee -a "$LOG_FILE"
if command -v omnikey >/dev/null 2>&1; then
    omnikey list | tee -a "$LOG_FILE"
fi

# 4. Verify Hermes Agent Health
echo "--- [4/7] Checking Hermes Health ---" | tee -a "$LOG_FILE"
hermes doctor || true
systemctl --user is-active --quiet hermes-gateway || systemctl --user restart hermes-gateway
sudo systemctl is-active --quiet hermes-dashboard || sudo systemctl restart hermes-dashboard

# 5. Database Optimization & Compact
echo "--- [5/7] Compacting SQLite Databases ---" | tee -a "$LOG_FILE"
for db in ~/.hermes/*.db ~/.hermes/cron/*.db ~/.omniroute/*.sqlite; do
    if [ -f "$db" ]; then
        python3 -c "import sqlite3; c=sqlite3.connect('$db'); c.execute('PRAGMA optimize;'); c.execute('PRAGMA wal_checkpoint(TRUNCATE);'); c.close()" 2>/dev/null || true
    fi
done

# 6. Storage Hygiene & Log Rotation
echo "--- [6/7] Reclaiming Storage & Trimming Logs ---" | tee -a "$LOG_FILE"
sudo journalctl --vacuum-size=100M >/dev/null 2>&1 || true
rm -rf /tmp/*.tmp /tmp/*.log 2>/dev/null || true
find ~/.hermes/logs -type f -name "*.log" -size +10M -exec truncate -s 5M {} + 2>/dev/null || true

# 7. Memory Reclamation
echo "--- [7/7] Memory Status & Hygiene ---" | tee -a "$LOG_FILE"
sudo sync
sudo sh -c 'echo 3 > /proc/sys/vm/drop_caches'
free -h | tee -a "$LOG_FILE"
df -h / | tee -a "$LOG_FILE"

echo "=== [$(date)] Maintenance Finished Successfully ===" | tee -a "$LOG_FILE"
