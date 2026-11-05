#!/usr/bin/env bash
# =============================================================================
# OmniRoute Playwright Security Patch Script
# Bypasses CSP restrictions for headless browser-backed clean-room executors
# =============================================================================

set -e

CHUNKS_DIR="/usr/lib/node_modules/omniroute/dist/.build/next/server/chunks"

if [ ! -d "$CHUNKS_DIR" ]; then
    echo "[!] Chunks directory not found at $CHUNKS_DIR"
    exit 0
fi

echo "[*] Patching Playwright launch arguments in OmniRoute chunks..."

sudo node << 'EOF'
import fs from 'fs';
import path from 'path';

const dir = '/usr/lib/node_modules/omniroute/dist/.build/next/server/chunks';
const files = fs.readdirSync(dir).filter(f => f.endsWith('.js'));

let patchedCount = 0;
for (const file of files) {
    const fullPath = path.join(dir, file);
    let content = fs.readFileSync(fullPath, 'utf8');
    const target = 'args:["--no-sandbox","--disable-dev-shm-usage"';
    if (content.includes(target) && !content.includes('--disable-web-security')) {
        content = content.replace(target, 'args:["--no-sandbox","--disable-web-security","--disable-dev-shm-usage"');
        fs.writeFileSync(fullPath, content, 'utf8');
        patchedCount++;
        console.log(`[+] Patched ${file}`);
    }
}
console.log(`[*] Total chunks patched with --disable-web-security: ${patchedCount}`);
EOF

echo "[+] Security patch step complete."

