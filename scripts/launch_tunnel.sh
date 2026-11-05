#!/usr/bin/env bash
# ==============================================================================
# OmniRoute Public Tunnel Launcher (Cloudflare Quick Tunnel)
# ==============================================================================

LOG_FILE="/home/arush/.omniroute/tunnel.log"
URL_FILE="/home/arush/.omniroute/public_url.txt"

echo "[$(date)] Starting OmniRoute Cloudflare Tunnel to http://127.0.0.1:20128..." >> "$LOG_FILE"

# Run cloudflared in the background and pipe output
/usr/local/bin/cloudflared tunnel --url http://127.0.0.1:20128 2>&1 | while read -r line; do
    echo "$line" >> "$LOG_FILE"
    # Check for the trycloudflare URL pattern
    if [[ "$line" =~ (https://[a-zA-Z0-9-]+\.trycloudflare\.com) ]]; then
        TUNNEL_URL="${BASH_REMATCH[1]}"
        echo "$TUNNEL_URL" > "$URL_FILE"
        chmod 644 "$URL_FILE"
        echo "[$(date)] Public URL detected and saved: $TUNNEL_URL" >> "$LOG_FILE"
    fi
done

