---
name: growth-manager
description: "Autonomous Growth Manager & Weekly Optimization Engine for Arush Sengar. Performs weekly audits of LinkedIn and X engagement, diagnoses bottlenecks (e.g. posts plateauing at ~30 views), applies context-aware smart company @tagging, and directs daily 7:00 AM IST synchronized multi-platform publishing."
version: 1.0.0
---

# growth-manager (God-Mode v1.0)

## Core Capabilities
1. **Weekly Engagement & Growth Auditing (`growth_manager.py`)**:
   - Gathers 7-day post metrics (views, likes, comments, engagement rate) across LinkedIn & X.
   - Detects low-impression bottlenecks (e.g. posts stuck around ~30–50 views).
   - Generates actionable tuning directives saved to `~/.hermes/growth_manager_directives.json`.
   - Records weekly audit reports into the Django Hub (`WeeklyGrowthReview` model).

2. **Context-Aware Smart Tagging (`smart_tagger.py`)**:
   - Automatically detects organizations, lab platforms, universities, and tool vendors from topic context:
     - `@Galgotias University` (University affiliation & student builder context)
     - `@Cyber Secured India` & `@SafeSkillz` (Internship milestones & mentors)
     - `@TryHackMe`, `@Hack The Box`, `@OffSec` (Lab writeups & rooms)
     - `@The Linux Foundation`, `@Python Software Foundation`, `@Docker, Inc`, `@Cloudflare` (Tech topics)
   - Injects targeted mentions (`cc: @Company`) to trigger employee reactions, recruiter visibility, and organic company reshares.

3. **3 Content Pillars (Varied Student Builder Tone)**:
   - **Pillar 1: Hands-On Labs & Assignments** (TryHackMe, OWASP, SUID exploit breakdown).
   - **Pillar 2: Real-World Homelab & Systems** (Raspberry Pi 4 4GB limits, zram swap, Docker microservices).
   - **Pillar 3: AI & Systems Research** (Local LLM routing latency, prompt injection defenses, kernel eBPF).

4. **Synchronized 7:00 AM IST Daily Execution**:
   - Master unified pipeline: `python3 /home/arush/omni_daily_growth.py`.
   - Scheduled daily via Raspberry Pi Cron at 7:00 AM IST (`0 7 * * *`).
   - Weekly Manager Review scheduled Sunday 8:00 PM IST (`0 20 * * 0`).

## CLI Commands (on Raspberry Pi)
```bash
# 1. Run Weekly Growth Manager Audit & Optimization Report
python3 /home/arush/growth_manager.py

# 2. Run Daily Unified Growth Pipeline (LinkedIn + X with Smart Tagging)
python3 /home/arush/omni_daily_growth.py

# 3. Dry-Run with Fresh Autonomous Topic Research
python3 /home/arush/omni_daily_growth.py --dry-run --research

# 4. View Real-Time Web Dashboard
# Open http://192.168.0.100:8000 in your browser
```

