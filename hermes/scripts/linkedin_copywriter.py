#!/usr/bin/env python3
"""
linkedin_copywriter.py — Generates humanized, high-credibility LinkedIn posts for Arush Sengar.
Handles two distinct modes:
  Mode A: Assignment Posts (milestone celebration, TryHackMe/OWASP, Cyber Secured India, SafeSkillz)
  Mode B: Autonomous / Independent Posts (Homelab, AI Security, Linux, Dev, Architecture — NO internship mention)
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

MODEL = os.environ.get("DAILY_MODEL", "auto/best-chat")

SYSTEM_PROMPT = """You are Arush Sengar, an ambitious 1st-year BCA Cyber Security student at Galgotias University, self-taught builder, and cyber security enthusiast learning in public.

POST STRUCTURE GUIDELINES:

IF THE TOPIC IS AN INTERNSHIP ASSIGNMENT:
- Open with: "🚀 Completed Assignment-[X]: [Topic] as part of my cybersecurity internship with Cyber Secured India & SafeSkillz!"
- Breakdown the specific lab tools and platforms (TryHackMe, OWASP MAS, etc.).
- 3-4 bullet takeaways.
- Mentor gratitude to Cyber Secured India, SafeSkillz, and Galgotias University.
- Engaging question + 6-8 hashtags.

IF THE TOPIC IS A NON-INTERNSHIP POST (Homelab, AI Security, Sysadmin, Linux Engineering, Coding Projects):
- STRICT: DO NOT MENTION ANY INTERNSHIP OR ASSIGNMENT NUMBERS.
- Open with a sharp, compelling builder hook (e.g. "🚀 Running an autonomous AI homelab on a 4GB Raspberry Pi 4 taught me more about Linux memory management than any unlimited cloud instance.")
- Explain the real technical challenge faced (e.g. OOM kills, memory limits under multi-model routing, prompt injection guardrail bypass, network security).
- Explain how you solved it (e.g. zram swap, systemd watchdog, process pruning, indirect prompt steering).
- 3 punchy, high-signal technical bullets.
- Mention being a BCA Cyber Security student at Galgotias University building in public.
- Engaging community discussion question.
- 6-8 targeted hashtags (e.g. #RaspberryPi #Homelab #DevOps #CyberSecurity #Linux #StudentBuilder #GalgotiasUniversity #BuildingInPublic).

STRICT RULES FOR ALL POSTS:
- NEVER mention filenames or file extensions (no '.docx', no 'Global_Internship...').
- NEVER sound like a generic corporate bot.
- Keep length around 180-250 words.
"""

def generate_post(topic_data: dict, angle_modifier: str = "") -> tuple:
    topic = topic_data.get("topic", "Cyber Security Engineering")
    assignment_num = topic_data.get("assignment_num", "")
    source = topic_data.get("source", "")
    platform = topic_data.get("platform", "")
    context = topic_data.get("context", "")
    labs = topic_data.get("labs", [])
    
    is_assignment = bool(assignment_num) and ("intern" in str(context).lower() or source == "assignment")
    
    labs_str = "\n".join(labs) if labs else ""
    
    user_prompt = f"""Write an engaging LinkedIn post for:
Topic: {topic}
Is Internship Assignment: {is_assignment}
Assignment Number: {assignment_num if is_assignment else 'None (Independent Student Post)'}
Platform/Environment: {platform}
Specific Details / Context:
{labs_str}
{context}

{angle_modifier}

On the very last line, output an AI visual prompt for OmniRoute that describes a clean, cinematic 3D cyber visual matching this topic (NO text in image). Format as:
IMAGE_PROMPT: <detailed 3D visual prompt>

Output ONLY the post followed by IMAGE_PROMPT."""

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 1000
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
    thesis = re.sub(r'^[🚀\s\-•*]+', '', first_line)[:55].strip()
    
    return clean_post, thesis, image_prompt

def validate_post(post: str) -> tuple:
    if not post:
        return False, "Post is empty"
    words = post.split()
    if len(words) < 70:
        return False, f"Post too short ({len(words)} words)"
    if len(words) > 380:
        return False, f"Post too long ({len(words)} words)"
    banned = [".docx", "as an ai", "i am an ai", "chatgpt", "deepseek", "language model"]
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
    print("\n=== IMAGE PROMPT ===")
    print(ip)
