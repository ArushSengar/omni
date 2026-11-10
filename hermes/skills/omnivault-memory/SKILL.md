---
name: omnivault-memory
description: "Hermes Agent Multimodal Tool Memory & OmniVault Knowledge Bank on Port 8000. Autonomously ingests screenshots, images, web links, and technical tricks into OmniVault with OCR, AI categorization, and 1-line purpose summaries so Arush never has to manually open the browser. Queries stored tools and tracks AI provider wallet quotas."
version: 1.0.0
---

# omnivault-memory (God-Mode v1.0)

## Core Capabilities
1. **Autonomous Image & Screenshot Ingestion (`hermes-omnivault ingest-image <path>`)**:
   - When Arush provides an image, photo, or screenshot of a website, tool, code snippet, or cheat-sheet:
     - DO NOT ask him to upload it to the website manually.
     - Execute: `python3 /home/arush/hermes_omnivault.py ingest-image "<path>" --json`
     - The engine runs OCR via Tesseract, parses the technical features with OmniRoute AI, checks for duplicates, and creates a clean `VaultResource` in the Omni Hub database on Port 8000.
     - Produces a crisp 1-line purpose summary: *"Maine yeh tool OmniVault mein save kar diya hai: [Title] — [1-Line Purpose]"*.

2. **Web URL & Technical Note Ingestion (`hermes-omnivault ingest-url <url>`)**:
   - Ingests URLs directly with live metadata crawling, safety verification (SAFE vs PENTEST_ONLY vs CAUTION), and categorization into 7 canonical technical domains:
     - `AI & LLM Tools`
     - `Cyber Security & Pentesting`
     - `Developer & APIs`
     - `Media, Audio & Design`
     - `Linux, Homelab & Systems`
     - `Productivity & Cloud`
     - `Student & Learning`

3. **Natural Language Tool Retrieval (`hermes-omnivault search "<query>"`)**:
   - When Arush asks: "Mujhe audio split karne wali site batao jo save ki thi", execute:
     `python3 /home/arush/hermes_omnivault.py search "audio split vocal remove" --json`
   - Returns the exact tool name, category, direct link, and 1-line description.

4. **Omni Hub AI Wallet & System Telemetry (`hermes-omnivault wallet` / `status`)**:
   - Live query of all 11 model providers, active routing tiers, and dollar savings.
   - Live Pi 4 hardware metrics (CPU Temp, RAM %, Disk space).

## CLI Reference (Raspberry Pi & Hermes Environment)
```bash
# 1. Ingest screenshot with OCR & AI synthesis
python3 /home/arush/hermes_omnivault.py ingest-image /path/to/screenshot.png

# 2. Ingest URL
python3 /home/arush/hermes_omnivault.py ingest-url https://example.com/tool

# 3. Ingest Note / Cheat-Sheet
python3 /home/arush/hermes_omnivault.py ingest-note "CyberChef recipe for base64 decode" --title "CyberChef Base64"

# 4. Search Knowledge Base
python3 /home/arush/hermes_omnivault.py search "OSINT tools"

# 5. Inspect AI Wallet
python3 /home/arush/hermes_omnivault.py wallet

# 6. Check System Status
python3 /home/arush/hermes_omnivault.py status
```
