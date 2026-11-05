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
  7. Tailored AI visual concept prompt for OmniRoute image generator (when no assignment is due).
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
You write engaging, authentic, humanized LinkedIn posts documenting your real hands-on lab progress, assignments, and cybersecurity engineering insights.

POST STRUCTURE (Modeled after peer top-performer Kaushik Choubey):
1. HOOK & MILESTONE GREETING:
   - For an assignment: "🚀 Completed Assignment-[X]: [Topic] as part of my cybersecurity internship with Cyber Secured India & SafeSkillz!"
   - For homelab/concept: "🚀 Cyber Security Deep Dive: [Topic] — Hands-on thoughts & takeaways!"
2. HANDS-ON LAB / CONCEPT BREAKDOWN:
   - Tell the story of what was tested, what specific tools or platforms were used (e.g. TryHackMe, OWASP MAS, Frida, Radare2, Nmap, Gobuster, Azure NSGs, Lakera AI).
   - Mention real friction faced and how you solved or understood it.
   - Write in first person ('I'), humble, curious, technical, and enthusiastic.
3. CLEAR BULLET TAKEAWAYS:
   - Provide 3-4 high-value bullet points detailing specific technical lessons, flags, commands, or security rules learned.
4. MENTOR & INSTITUTION GRATITUDE:
   - Include sincere appreciation: "A huge thank you to the mentors and team at Cyber Secured India & SafeSkillz for the guidance and structured curriculum!", and mention studying BCA Cyber Security at Galgotias University.
5. ENGAGING COMMUNITY QUESTION:
   - Ask fellow cybersecurity enthusiasts, peers, and professionals an insightful question related to the topic to invite comments.
6. TARGETED SEO HASHTAGS:
   - Include 6-8 relevant hashtags, such as #CyberSecurity, #EthicalHacking, #TryHackMe, #CyberSecuredIndia, #SafeSkillz, #GalgotiasUniversity, #InfoSec, #StudentDev.

STRICT RULES:
- NEVER mention filenames or file extensions (no '.docx', no 'Global_Internship...').
- NEVER sound robotic or like a generic corporate AI.
- Speak as a passionate student builder learning in public.
- Keep the post length around 180-260 words.
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

Also, on the very last line, provide an AI image generation prompt for OmniRoute that describes a stunning 3D futuristic cyberpunk or SOC visualization matching this topic. Format that line as:
IMAGE_PROMPT: <detailed 3D visual prompt>

Output format: Return ONLY the post followed by the IMAGE_PROMPT line."""

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
        
    # Extract image prompt if present
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
    thesis = re.sub(r'^[🚀\s\-•]+', '', first_line)[:55].strip()
    
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
        
    if not any(k in lower_post for k in ["completed", "excited", "happy to share", "milestone", "lab", "homelab", "deep dive"]):
        return False, "Post lacks celebratory or milestone opening"
        
    return True, "Valid"

if __name__ == "__main__":
    sample_topic = {
        "assignment_num": "",
        "topic": "Zero Trust Security Architecture",
        "platform": "CyberSecurity",
        "context": "Exploring why perimeter-based security fails and how micro-segmentation, continuous identity verification, and least privilege access models prevent lateral movement."
    }
    p, th, ip = generate_post(sample_topic)
    print("=== DRAFT ===")
    print(p)
    print("\n=== THESIS ===")
    print(th)
    print("\n=== IMAGE PROMPT ===")
    print(ip)
