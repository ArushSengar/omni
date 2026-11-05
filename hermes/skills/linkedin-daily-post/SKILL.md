---
name: linkedin-daily-post
description: "Arush's God-Tier daily LinkedIn engine: scans real assignments & labs, composes humanized peer-benchmark posts (Kaushik Choubey formula), renders branded proof-of-work collages, and posts via Composio CLI."
version: 3.0.0
---

# linkedin-daily-post (God-Mode v3.0)

## Architecture & Workflow (November 2026)
1. **Activity & Milestone Detection (`linkedin_activity_detector.py`)**:
   - Scans `/home/arush/assignments_archive/documents/*.docx` and active lab reports.
   - Extracts assignment number, topic, sub-labs, reflection text, and screenshots from `/home/arush/assignment_media/`.
   - Checks `~/posts/notes.md` or `~/posts/today_notes.txt` for live quick notes dropped by Arush.
   - Rotates through real student experiences (TryHackMe, OWASP MAS, Azure NSG Cloud Defense, Lakera AI Prompt Injection, Raspberry Pi 4 Homelab).

2. **Tone & Humanized Copywriting (`linkedin_copywriter.py`) — The Kaushik Formula**:
   - **Identity**: 1st-year BCA Cyber Security student at Galgotias University, Cyber Security Intern at Cyber Secured India & SafeSkillz.
   - **Milestone Greeting**: Opens with celebration & gratitude:
     `🚀 Completed Assignment-[X]: [Topic] as part of my cybersecurity internship with Cyber Secured India & SafeSkillz!`
     (or `🚀 Homelab Milestone: ...` for server architecture days).
   - **Hands-on Lab Story**: Describes real friction, tools used (`nmap -sV -sC`, `bash -p`, `GTFOBins`, `Frida`, `LinPEAS`, `Azure NSG`), and how challenges were resolved.
   - **3-4 Punchy Bullets**: High-value technical takeaways for fellow students and practitioners.
   - **Mentor & Community Gratitude**: Expresses sincere appreciation to mentors at Cyber Secured India, SafeSkillz, and Galgotias University.
   - **Community Question**: Asks peers an engaging question to foster networking and insightful replies.
   - **SEO Hashtags**: 6-8 relevant hashtags (`#CyberSecurity #EthicalHacking #TryHackMe #CyberSecuredIndia #SafeSkillz #GalgotiasUniversity #InfoSec #StudentDev`).

3. **Proof-of-Work Collages (`linkedin_collage_generator.py`) — ZERO Stock Photos**:
   - **NEVER use generic Wikimedia Commons or Pexels photos** (museum engines, abstract locks, etc. are strictly forbidden).
   - **Quad Collage (2x2 Grid)**:
     - Top-Left: Branded Header Card with Cyber Secured India, SafeSkillz, and Galgotias University badges, assignment info, candidate name ("Arush Sengar"), and verified badge.
     - Top-Right, Bottom-Left, Bottom-Right: High-resolution screenshots of TryHackMe badges, room completions, terminal scans, and flag captures.
   - **3-Column Banner**: Top header banner with 3 mobile/emulator screenshots (OWASP MAS / Android / iOS).
   - **Homelab Proof Card**: For system administration posts, generates a live dark terminal dashboard with real Raspberry Pi 4 metrics (systemd status of omniroute, uptime, RAM allocation, CPU load), proving genuine engineering credibility.

4. **Publishing**:
   - Primary: **Composio CLI** (`LINKEDIN_CREATE_LINKED_IN_POST` with `images: [collage_path]`).
   - Fallback: Playwright (`~/linkedin_autopost.py`).

5. **Execution**:
   - Dry-run validation: `python3 ~/linkedin_daily_post.py --dry-run`
   - Specific assignment: `python3 ~/linkedin_daily_post.py --assignment 7 --dry-run`
   - Daily production post: `python3 ~/linkedin_daily_post.py`
   - Hermes Daily Cron: `35a18463b414` scheduled at 10:00 AM IST daily.
   - Post logs & archives: `~/posts/daily/YYYYMMDD_HHMM.md` and `~/.hermes/linkedin_daily/daily_learnings.json`.
