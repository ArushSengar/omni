#!/usr/bin/env bash
# =============================================================================
# OmniRoute Automated Deployment & Setup Script for Raspberry Pi (Debian arm64)
# =============================================================================

set -e

echo "[*] Initializing OmniRoute Setup for Raspberry Pi..."

# 1. Install System Dependencies
echo "[*] Checking and installing system packages..."
sudo apt-get update -y
sudo apt-get install -y chromium curl sqlite3 ca-certificates jq

# 2. Setup OmniRoute Directory
OMNI_DIR="$HOME/.omniroute"
mkdir -p "$OMNI_DIR"

# 3. Create or Update .env
if [ ! -f "$OMNI_DIR/.env" ]; then
    echo "[*] Creating new .env configuration..."
    cat << 'EOF' > "$OMNI_DIR/.env"
STORAGE_ENCRYPTION_KEY=94cdc28ee5c868d60e5e36b6b6c895a0bb90dfc6eefee24e964ccfc8656268d6
HOSTNAME=0.0.0.0
PORT=20128
CLOUDFLARE_PLAYGROUND_CHROME_PATH=/usr/bin/chromium
PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH=/usr/bin/chromium
EOF
else
    echo "[+] Existing .env found, preserving credentials."
    # Ensure Chromium paths exist
    grep -q "CLOUDFLARE_PLAYGROUND_CHROME_PATH" "$OMNI_DIR/.env" || echo "CLOUDFLARE_PLAYGROUND_CHROME_PATH=/usr/bin/chromium" >> "$OMNI_DIR/.env"
    grep -q "PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH" "$OMNI_DIR/.env" || echo "PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH=/usr/bin/chromium" >> "$OMNI_DIR/.env"
fi

# 4. Check OmniRoute Global Installation
if ! command -v omniroute &> /dev/null; then
    echo "[*] OmniRoute not found in PATH. Installing via npm..."
    sudo npm install -g omniroute
else
    echo "[+] OmniRoute is already installed: $(omniroute -v 2>/dev/null || echo 'v3.8.52')"
fi

# 5. Apply Security Patches for Playwright Clean-room Executors
echo "[*] Applying Playwright security flags..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$SCRIPT_DIR/patch_playwright_security.sh" ]; then
    bash "$SCRIPT_DIR/patch_playwright_security.sh"
fi

# 6. Restart Service
echo "[*] Restarting OmniRoute..."
pkill -9 -f 'omniroute' || true
sleep 3

# Wait for startup
echo "[*] Verifying gateway health..."
for i in {1..10}; do
    if curl -s http://127.0.0.1:20128/api/health | grep -q "ok"; then
        echo "[+] OmniRoute Gateway is UP and Healthy on port 20128!"
        exit 0
    fi
    sleep 2
done

echo "[-] Gateway took longer than expected to start. Check: omniroute logs"

