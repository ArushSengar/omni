---
name: linkedin-daily-post
description: "Arush's God-Tier daily LinkedIn growth engine: humanized student-builder storytelling, zero AI buzzwords, pure document collages for assignments, and authentic dark-mode terminal proof cards for engineering & homelab days."
version: 3.3.0
---

# linkedin-daily-post (God-Mode v3.3)

## Core Philosophy & Tone Rules
1. **100% Humanized, Grounded Voice**:
   - Written strictly as Arush Sengar (1st-year BCA Cyber Security student @ Galgotias University, self-taught builder).
   - **FORBIDDEN AI CLICHÉS**:
     - No opening rocket emojis (🚀) or emojis on every line.
     - No bullet points starting with diamond or flame emojis (🔹, 💡, 🔥).
     - No ChatGPT corporate speak ("without breaking a sweat", "rock-solid", "game-changer", "delve into", "seamlessly", "harnessing", "unlock", "wild ride").
   - **STRUCTURE**:
     - Candid real hook (friction, mystery, crash, or unexpected behavior).
     - Diagnosis (what was actually happening under the hood).
     - Concrete fix (numbered 1-2-3 list with real tools, commands, or configs).
     - Real outcome & numbers (load average, memory headroom, throughput, 0 crashes).
     - Authentic takeaway from building on real hardware or practical labs.
     - Genuine peer question to spark discussions.
     - 5-6 clean, focused domain hashtags.

2. **Visual Standards — ZERO Stock Photos & ZERO Synthetic Text Overlays**:
   - **Mode A (Assignment Days)**:
     - Pure collage of real screenshots from `/home/arush/assignment_media/` or extracted DOCX reports.
     - Single image: cleanly centered on the 1200x1200 canvas.
     - 2 images: split horizontal.
     - 3 images: hero top + 2 bottom split.
     - 4+ images: 2x2 seamless grid.
     - **NEVER draw synthetic headers, candidate names, or status pills over uploaded images.**
   - **Mode B (Autonomous Builder Days — Non-Assignment)**:
     - Dynamically rendered **Authentic Dark-Mode Terminal Proof Card** (1200x1200 square).
     - Tailored to domain:
       * **Homelab / Linux**: live Pi stats (`uname -rm`, `systemctl status omniroute`, `free -h`, `uptime`, `watchdog.py`).
       * **Cyber Security & Pentesting**: recon & audit (`nmap -sV -sC`, `ss -tulpn`, `ufw status`, `security_audit.py`).
       * **Software Engineering & Python**: testing & profiling (`pytest`, `tracemalloc`, clean `git log`).
       * **Networking & Protocols**: latency & DNS (`curl -w`, `ip route`, `ping`, `dig`).
       * **Databases & DevOps**: storage & WAL mode (`sqlite3 WAL`, `df -h tmpfs`, `systemctl list-timers`).
     - Features macOS style traffic lights (🔴 🟡 🟢), emerald prompts (`arush@pi4:~$`), cyan parameters, amber memory metrics, crisp DejaVu monospace typography, and active cursor.

3. **Topic Discovery & Rotation Pipeline (`linkedin_activity_detector.py`)**:
   - Priority 1: Unposted internship assignments from `/home/arush/assignments_archive/documents/*.docx`.
   - Priority 2: Live quick notes dropped by Arush in `~/posts/notes.md` or `~/posts/today_notes.txt`.
   - Priority 3: Curated multi-domain engineering backlog (Homelab, Python internals, SQLite WAL mode, DNS latency, Linux privilege escalation, UFW hardening, AsyncIO architecture, Bash error traps, Lakera prompt injection, Student builder journey).
   - Priority 4: Re-visiting complex assignment labs with fresh technical angles.

4. **Publishing Pipeline (`linkedin_daily_post.py`)**:
   - Primary: **Composio CLI** (`LINKEDIN_CREATE_LINKED_IN_POST` with attached image).
   - Author URN: `urn:li:person:qzJKgZnzTh`.
   - Fallback: Playwright (`~/linkedin_autopost.py`).
   - Daily archives: `~/posts/daily/YYYYMMDD_HHMM.md` and `~/.hermes/linkedin_daily/daily_learnings.json`.

5. **Hermes Integration & Execution**:
   - Run manually: `python3 ~/linkedin_daily_post.py`
   - Run dry-run: `python3 ~/linkedin_daily_post.py --dry-run`
   - Force specific topic: `python3 ~/linkedin_daily_post.py --topic "<Topic Name>"`
   - Daily cron: Hermes job `35a18463b414` set for 10:00 AM IST daily.
