#!/usr/bin/env python3
"""
linkedin_copywriter.py — Generates humanized, high-credibility LinkedIn posts for Arush Sengar.
Modeled after high-performing peer benchmarks (Kaushik Choubey formula):
  1. Milestone greeting & celebratory hook
  2. Authentic student lab breakdown
  3. Key practical takeaways (tools, commands, principles)
  4. Mentor gratitude (Cyber Secured India, SafeSkillz, Galgotias University)
  5. Interactive community discussion question
  6. Targeted, SEO-friendly hashtags
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

SYSTEM_PROMPT = """You are Arush Sengar, a 1st-year BCA Cyber Security student at Galgotias University and Cyber Security Intern at Cyber Secured India & SafeSkillz.
You write engaging, authentic, humanized LinkedIn posts documenting your real hands-on lab progress and assignments.

POST STRUCTURE (Modeled after peer top-performer Kaushik Choubey):
1. HOOK & MILESTONE GREETING:
   - For an assignment: "🚀 Completed Assignment-[X]: [Topic] as part of my cybersecurity internship with Cyber Secured India & SafeSkillz!"
   - For homelab/project: "🚀 Homelab Update: [Topic] — Building & hardening my 24/7 Raspberry Pi 4 environment!"
2. HANDS-ON LAB BREAKDOWN:
   - Tell the story of what was tested, what specific tools or platforms were used (e.g. TryHackMe, OWASP MAS, Frida, Radare2, Nmap, Gobuster, Azure NSGs, Lakera AI).
   - Mention real friction faced and how you solved or understood it.
   - Write in first person ('I'), humble, curious, technical, and enthusiastic.
3. CLEAR BULLET TAKEAWAYS:
   - Provide 3-4 high-value bullet points detailing specific technical lessons, flags, commands, or security rules learned.
4. MENTOR & INSTITUTION GRATITUDE:
   - Include sincere appreciation: "A huge thank you to the mentors and team at Cyber Secured India & SafeSkillz for the guidance and structured curriculum!", and mention studying BCA Cyber Security at Galgotias University.
5. ENGAGING COMMUNITY QUESTION:
   - Ask fellow cybersecurity enthusiasts, peers, and professionals an insightful question related to the lab topic to invite comments.
6. TARGETED SEO HASHTAGS:
   - Include 6-8 relevant hashtags, such as #CyberSecurity, #EthicalHacking, #TryHackMe (or relevant platform), #CyberSecuredIndia, #SafeSkillz, #GalgotiasUniversity, #InfoSec, #StudentDev.

STRICT RULES:
- NEVER mention filenames or file extensions (no '.docx', no 'Global_Internship...').
- NEVER sound robotic or like a generic corporate AI.
- Speak as a passionate student builder learning in public.
- Keep the length around 180-260 words — crisp, readable, easy to skim on mobile.
"""

def generate_post(topic_data: dict, angle_modifier: str = "") -> tuple:
    topic = topic_data.get("topic", "Cyber Security Hands-on Lab")
    assignment_num = topic_data.get("assignment_num", "")
    platform = topic_data.get("platform", "Hands-on Lab")
    context = topic_data.get("context", "")
    labs = topic_data.get("labs", [])
    
    labs_str = "\n".join(labs) if labs else ""
    
    user_prompt = f"""Write a LinkedIn post with the Kaushik Choubey formula for:
Assignment Number: {assignment_num}
Topic: {topic}
Platform: {platform}
Specific Labs:
{labs_str}
Hands-on Reflection & Context:
{context}

{angle_modifier}

Output ONLY the final LinkedIn post ready to publish. No conversational preambles or notes."""

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
        raw_post = res["choices"][0]["message"]["content"].strip()
        
    # Clean any stray docx references if any leaked
    clean_post = re.sub(r'[\w\-]+\.docx', '', raw_post).strip()
    
    # Extract first line as thesis
    first_line = clean_post.split("\n")[0].strip()
    # Remove leading rocket emoji or characters for thesis hook
    thesis = re.sub(r'^[🚀\s\-•]+', '', first_line)[:55].strip()
    
    return clean_post, thesis

def validate_post(post: str) -> tuple:
    """Validates word count, banned words, structure."""
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
            
    # Check for hashtags
    if "#" not in post:
        return False, "Post missing hashtags"
        
    # Check for greeting/hook
    if not any(k in lower_post for k in ["completed", "excited", "happy to share", "milestone", "lab", "homelab"]):
        return False, "Post lacks celebratory or milestone opening"
        
    return True, "Valid"

if __name__ == "__main__":
    sample_topic = {
        "assignment_num": "10",
        "topic": "iOS Pentesting",
        "platform": "OWASP Mobile Application Security (MAS)",
        "labs": ["Lab 1: iOS UnCrackable Level 1"],
        "context": "Learned how apps detect jailbreak environments and runtime tampering using Frida and static decompilation."
    }
    p, th = generate_post(sample_topic)
    print("=== DRAFT ===")
    print(p)
    print("\n=== THESIS ===")
    print(th)
    ok, why = validate_post(p)
    print(f"\nValidation: {ok} ({why})")
