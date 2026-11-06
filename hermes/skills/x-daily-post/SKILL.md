---
name: x-daily-post
description: "Arush's autonomous X (Twitter) growth engine: high-impact tech tweets & viral 3-tweet threads (<280 chars), zero AI fluff, authentic dark-mode terminal cards, pure assignment screenshot collages, and automated Composio publishing with in-reply-to thread chaining."
version: 1.0.0
---

# x-daily-post (God-Mode v1.0)

## Core Philosophy & Voice Rules on X (Twitter)
1. **Engineered for High-Signal #TechTwitter & #BuildInPublic**:
   - Voice: Arush Sengar (1st-year BCA Cyber Security student @ Galgotias University, hands-on homelab builder, cyber security intern).
   - **Scroll-Stopping First Line**: The hook must be direct, raw, and highlight a real technical challenge, friction, latency stat, or TryHackMe/OWASP milestone.
   - **Strict Character Limits**: Every single tweet MUST be under 280 characters (recommended: 140–260 chars for high readability).
   - **Zero AI Buzzwords**: No "delve", "game-changer", "without breaking a sweat", "rock-solid", or corporate marketing speak.
   - **Real Commands & Snippets**: Always include practical commands (e.g. `find / -perm -4000`, `zramctl`, `sqlite3 :memory:`, `nmap -sV`).

2. **Supported Formats**:
   - **Mode 1: Single Punchy Tweet (`--single`)**:
     - Fast, high-impact hook + technical insight + 2 targeted hashtags (e.g., `#CyberSecurity #BuildInPublic`).
     - Accompanied by Proof-of-Work visual (Terminal proof card or Lab screenshot collage).
   - **Mode 2: Viral 3-Tweet Mini-Thread (`--thread`)**:
     - **Tweet 1 (Hook + Media)**: The technical challenge, milestone, or lab breakdown with a thread indicator (👇 or 🧵).
     - **Tweet 2 (The Meat)**: 1-2-3 actionable commands, diagnostic steps, or bypass logic.
     - **Tweet 3 (Takeaway & Discussion)**: Concrete takeaway for student builders + open question to the engineering community.
     - Automatically chained via `reply_in_reply_to_tweet_id`.

3. **Visual Engine**:
   - Reuses [`linkedin_collage_generator.py`](file:///c:/Users/Arush/OneDrive/Documents/omni/hermes/scripts/linkedin_collage_generator.py):
     - **Assignment Days**: Pure multi-screenshot collage from real lab evidence (zero synthetic overlays).
     - **Autonomous Builder Days**: Tailored Dark-Mode Terminal Proof Cards (1200x1200) matching Homelab, Cyber Pentest, Python Dev, Networking, or Database topics.

4. **Publishing Pipeline (`x_daily_post.py`)**:
   - Primary: **Composio CLI** (`TWITTER_UPLOAD_MEDIA` + `TWITTER_CREATION_OF_A_POST`).
   - Automated error detection: Prompts user to 1-click connect at `https://dashboard.composio.dev/arush_sengar/~/connect/apps/twitter?open=true`.
   - Thread chaining: Seamlessly links thread tweets using reply IDs.
   - Archiving: Saves markdown archives to `~/posts/x/` and tracks history in `~/.hermes/x_daily/daily_tweets.json`.

5. **CLI & Execution Commands on Pi**:
   ```bash
   # 1. Full auto single tweet (dry-run)
   python3 ~/x_daily_post.py --dry-run

   # 2. Full auto 3-tweet thread (dry-run)
   python3 ~/x_daily_post.py --dry-run --thread

   # 3. Force specific assignment lab
   python3 ~/x_daily_post.py --assignment 7

   # 4. Force custom engineering topic
   python3 ~/x_daily_post.py --topic "Optimizing kernel memory with zram and cgroups on Raspberry Pi 4"

   # 5. Connect Twitter account (1-Click)
   # Open https://dashboard.composio.dev/arush_sengar/~/connect/apps/twitter?open=true
   # Or run: composio link twitter
   ```

