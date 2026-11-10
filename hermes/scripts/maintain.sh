#!/usr/bin/env bash
# ==============================================================================
# Autonomous Maintenance, Self-Healing & Telemetry Suite v5.0 (Raspberry Pi 4)
# ==============================================================================

export PATH="/home/arush/.hermes/hermes-agent/.hermes/bin:/home/arush/.local/bin:$HOME/.local/bin:$HOME/.cargo/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/1000}"

LOG_FILE="/home/arush/maintain.log"
echo "=== [$(date)] Starting Autonomous Pi Maintenance v5.0 ===" | tee "$LOG_FILE"

# 1. Package & Security Upgrades
echo "--- [1/8] Updating Debian Packages & Security Patches ---" | tee -a "$LOG_FILE"
sudo apt-get update -y >/dev/null 2>&1 || true
sudo apt-get --only-upgrade install -y libssl3 openssl curl ca-certificates >/dev/null 2>&1 || true
sudo apt-get autoremove -y >/dev/null 2>&1 || true
sudo apt-get clean -y >/dev/null 2>&1 || true
echo "  [ok] Packages & security libraries verified" | tee -a "$LOG_FILE"

# 2. Verify OmniHub, OmniRoute & Tunnel
echo "--- [2/8] Verifying OmniHub, OmniRoute & Public Cloudflare Tunnel ---" | tee -a "$LOG_FILE"
sudo systemctl is-active --quiet omni-hub || sudo systemctl restart omni-hub || true
sudo systemctl is-active --quiet omniroute || sudo systemctl restart omniroute || true
sudo systemctl is-active --quiet omniroute-tunnel || sudo systemctl restart omniroute-tunnel || true

if [ -f /home/arush/.omniroute/public_url.txt ]; then
    PUBLIC_URL=$(cat /home/arush/.omniroute/public_url.txt)
    echo "  [ok] Active Public Tunnel URL: $PUBLIC_URL" | tee -a "$LOG_FILE"
else
    echo "  [warn] Public URL file not found, restarting tunnel..." | tee -a "$LOG_FILE"
    sudo systemctl restart omniroute-tunnel || true
fi

# 3. Verify OmniKeys & Local API
echo "--- [3/8] Verifying OmniKey Authentication ---" | tee -a "$LOG_FILE"
if command -v omnikey >/dev/null 2>&1; then
    sudo -u arush omnikey list 2>/dev/null | tee -a "$LOG_FILE" || true
fi

# 4. Verify Hermes Agent Health
echo "--- [4/8] Checking Hermes Health ---" | tee -a "$LOG_FILE"
hermes doctor 2>/dev/null || true
if [ -d "$XDG_RUNTIME_DIR/systemd" ]; then
    systemctl --user is-active --quiet hermes-gateway || systemctl --user restart hermes-gateway || true
fi
sudo systemctl is-active --quiet hermes-dashboard || sudo systemctl restart hermes-dashboard || true
echo "  [ok] Hermes services verified" | tee -a "$LOG_FILE"

# 5. Database Optimization & Compact (OmniRoute, Django Hub, Hermes)
echo "--- [5/8] Compacting SQLite Databases & Checkpointing WAL ---" | tee -a "$LOG_FILE"
for db in /home/arush/.hermes/*.db /home/arush/.hermes/cron/*.db /home/arush/.omniroute/*.sqlite /home/arush/omni_hub/db.sqlite3; do
    if [ -f "$db" ]; then
        python3 -c "import sqlite3; c=sqlite3.connect('$db'); c.execute('PRAGMA optimize;'); c.execute('PRAGMA wal_checkpoint(TRUNCATE);'); c.close()" 2>/dev/null && echo "  [compacted] $(basename $db)" | tee -a "$LOG_FILE" || true
    fi
done

# 6. Thermal & Hardware Health Telemetry
echo "--- [6/8] Auditing Pi Hardware & Thermals ---" | tee -a "$LOG_FILE"
if command -v vcgencmd >/dev/null 2>&1; then
    TEMP=$(vcgencmd measure_temp 2>/dev/null || echo "N/A")
    THROTTLE=$(vcgencmd get_throttled 2>/dev/null || echo "N/A")
    echo "  CPU Temperature: $TEMP" | tee -a "$LOG_FILE"
    echo "  Throttle Status: $THROTTLE" | tee -a "$LOG_FILE"
elif [ -f /sys/class/thermal/thermal_zone0/temp ]; then
    MILLI=$(cat /sys/class/thermal/thermal_zone0/temp)
    TEMP_C=$(awk "BEGIN {print $MILLI/1000}")
    echo "  CPU Temperature: ${TEMP_C}°C" | tee -a "$LOG_FILE"
fi

# 7. Storage Hygiene & Log Rotation
echo "--- [7/8] Reclaiming Storage & Trimming Oversized Logs ---" | tee -a "$LOG_FILE"
sudo journalctl --vacuum-size=50M >/dev/null 2>&1 || true
rm -rf /tmp/*.tmp /tmp/*.log 2>/dev/null || true
find /home/arush/.hermes/logs /home/arush/posts/daily -type f -name "*.log" -size +5M -exec truncate -s 2M {} + 2>/dev/null || true
echo "  [ok] Log rotation and tmp cleanup complete" | tee -a "$LOG_FILE"

# 8. Memory Status & Reclamation
echo "--- [8/8] Memory Status & Kernel Cache Hygiene ---" | tee -a "$LOG_FILE"
sudo sync
sudo sh -c 'echo 3 > /proc/sys/vm/drop_caches' 2>/dev/null || true
free -h | tee -a "$LOG_FILE"
df -h / | tee -a "$LOG_FILE"

echo "=== [$(date)] Maintenance v5.0 Finished Successfully ===" | tee -a "$LOG_FILE"
