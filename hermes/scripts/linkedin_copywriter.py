#!/usr/bin/env python3
"""
linkedin_copywriter.py — Generates humanized, high-credibility LinkedIn posts for Arush Sengar.
Handles two distinct modes:
  Mode A: Assignment Posts (milestone celebration, TryHackMe/OWASP, Cyber Secured India, SafeSkillz)
  Mode B: Autonomous / Independent Posts (Homelab, AI Security, Linux, Dev, Architecture — NO internship mention, 100% natural student builder voice)
"""

import os
import sys
# Strip stale python3.14 paths
sys.path = [p for p in sys.path if "python3.14" not in p]

import json
import re
import urllib.request
from pathlib import Path

BASE_URL = os.environ.get("OMNIROUTE_URL", "http://localhost:20128/v1")
API_KEY = os.environ.get("HERMES_CUSTOM_LOCALHOST_20128_API_KEY", "")

if not API_KEY and (Path.home() / ".hermes" / ".env").exists():
    try:
        for line in (Path.home() / ".hermes" / ".env").read_text().splitlines():
            if line.startswith("HERMES_CUSTOM_LOCALHOST_20128_API_KEY="):
                API_KEY = line.split("=", 1)[1].strip().strip('"').strip("'")
                break
    except Exception:
        pass

if not API_KEY:
    API_KEY = "sk-971230e546e14a3e-23822a-06e1aa8d"

MODEL = os.environ.get("DAILY_MODEL", "auto/best-chat")

SYSTEM_PROMPT = """You are Arush Sengar, a 1st-year BCA Cyber Security student at Galgotias University, self-taught builder, and authentic hands-on learner.

POST STRUCTURE GUIDELINES:

IF THE TOPIC IS AN INTERNSHIP ASSIGNMENT:
- Open with: "🚀 Completed Assignment-[X]: [Topic] as part of my cybersecurity internship with Cyber Secured India & SafeSkillz!"
- Breakdown the specific lab tools and platforms (TryHackMe, OWASP MAS, etc.).
- 3-4 bullet takeaways.
- Mentor gratitude to Cyber Secured India, SafeSkillz, and Galgotias University.
- Engaging question + 6-8 hashtags.

IF THE TOPIC IS A NON-INTERNSHIP POST (Homelab, Python Engineering, Databases, Networking, DevOps, AI Security, Student Builder):
- STRICT: DO NOT MENTION ANY INTERNSHIP OR ASSIGNMENT NUMBERS.
- STRICT: WRITE IN 100% NATURAL, CANDID, HUMAN BUILDER VOICE.
- FORBIDDEN AI CLICHÉS:
  * NO opening rocket emojis (🚀) or emojis at every heading/bullet.
  * NO bullet points starting with diamond or flame emojis (🔹, 💡, 🔥).
  * NO ChatGPT buzzwords: "without breaking a sweat", "rock-solid", "delve", "testament to", "game-changer", "dive deep", "seamlessly", "harnessing", "unlock", "wild ride".
  * NO corporate PR marketing tone.
- STRUCTURE:
  1. Real hook: start with the real technical friction or challenge you faced (e.g. database locks, memory leaks, DNS lookup latency, port enumeration deception, OOM kills).
  2. The diagnosis: what was actually happening under the hood.
  3. The concrete fix: simple numbered list (1, 2, 3) with real tools, configs, and commands (e.g. WAL mode, tracemalloc, unbound, zram, ufw).
  4. Real results: numbers or practical impact (latency, throughput, memory saved, stability).
  5. Practical takeaway: what building and breaking things teaches you as a 1st-year student builder at Galgotias University.
  6. Natural discussion question for fellow engineers and builders.
  7. 5-6 clean, targeted hashtags matching the domain.

STRICT RULES FOR ALL POSTS:
- NEVER mention filenames or file extensions (no '.docx', no 'Global_Internship...').
- NEVER sound like an AI marketing bot.
- Keep length strictly between 150 and 220 words. Be punchy, direct, and zero fluff.
"""

def generate_post(topic_data: dict, angle_modifier: str = "") -> tuple:
    topic = topic_data.get("topic", "Cyber Security Engineering")
    category = topic_data.get("category", "")
    assignment_num = topic_data.get("assignment_num", "")
    source = topic_data.get("source", "")
    platform = topic_data.get("platform", "")
    context = topic_data.get("context", "")
    labs = topic_data.get("labs", [])
    
    is_assignment = bool(assignment_num) and ("intern" in str(context).lower() or source == "assignment")
    labs_str = "\n".join(labs) if labs else ""
    
    if is_assignment:
        user_prompt = f"""Write an engaging LinkedIn post for:
Topic: {topic}
Category: {category or 'Cyber Security'}
Assignment Number: {assignment_num}
Platform/Environment: {platform}
Lab Details:
{labs_str}
{context}

{angle_modifier}

Output ONLY the final LinkedIn post."""
    else:
        user_prompt = f"""Write a completely natural, human, non-AI LinkedIn post about:
Topic: {topic}
Category: {category or 'Engineering & Homelab'}
Platform: {platform}
Technical Context:
{labs_str}
{context}

{angle_modifier}

Remember:
- NO rocket emojis, NO diamond bullet points, NO corporate buzzwords ("wild ride", "without breaking a sweat", "game changer").
- Sound like a real 19-year-old student builder sharing real debugging, tuning, and systems architecture.
- Always format the fix or solution as a clean numbered list (1, 2, 3) with exact tools/commands so it is scannable and authentic.
- Output ONLY the final LinkedIn post."""

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.6,
        "max_tokens": 850
    }

    req = urllib.request.Request(
        f"{BASE_URL}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}"
        }
    )

    with urllib.request.urlopen(req, timeout=60) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        raw_output = res["choices"][0]["message"]["content"].strip()
        
    image_prompt = ""
    lines = raw_output.splitlines()
    post_lines = []
    for line in lines:
        if line.strip().startswith("IMAGE_PROMPT:"):
            image_prompt = line.split("IMAGE_PROMPT:", 1)[1].strip()
        else:
            post_lines.append(line)
            
    raw_post = "\n".join(post_lines).strip()
    clean_post = re.sub(r'[\w\-]+\.docx', '', raw_post).strip()
    
    first_line = clean_post.split("\n")[0].strip()
    thesis = re.sub(r'^[🚀\s\-•*#]+', '', first_line)[:60].strip()
    
    return clean_post, thesis, image_prompt

def validate_post(post: str) -> tuple:
    if not post:
        return False, "Post is empty"
    words = post.split()
    if len(words) < 60:
        return False, f"Post too short ({len(words)} words)"
    if len(words) > 280:
        return False, f"Post too long ({len(words)} words, max 280)"
    banned = [".docx", "as an ai", "i am an ai", "chatgpt", "deepseek", "language model", "without breaking a sweat"]
    lower_post = post.lower()
    for b in banned:
        if b in lower_post:
            return False, f"Post contains forbidden term: '{b}'"
    if "#" not in post:
        return False, "Post missing hashtags"
    return True, "Valid"

if __name__ == "__main__":
    test_topic = {
        "topic": "Running an Autonomous AI Homelab on a 4GB Raspberry Pi 4",
        "assignment_num": "",
        "source": "backlog",
        "platform": "Raspberry Pi 4",
        "context": "Maintained my 24/7 Raspberry Pi 4 home server running OmniRoute AI proxy, systemd units, and local agents. Faced memory pressure with 4GB RAM under multi-model routing; implemented zram swap, container auto-pruning, and an automated self-healing watchdog daemon."
    }
    p, th, ip = generate_post(test_topic)
    print("=== DRAFT ===")
    print(p)
    print("\n=== THESIS ===")
    print(th)
