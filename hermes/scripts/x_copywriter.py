#!/usr/bin/env python3
"""
x_copywriter.py — High-Impact, Autonomous X (Twitter) Copywriting Engine for Arush Sengar.
Generates scroll-stopping, humanized tech content strictly adhering to Twitter limits (< 280 chars):
  - Format 1: Single Punchy Tweet (Hook + Technical insight + 2 hashtags)
  - Format 2: 3-Tweet Mini Thread (Hook/Problem -> 1-2-3 Technical Fix -> Takeaway & Question)
"""

import os
import sys

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

TWITTER_SYSTEM_PROMPT = """You are Arush Sengar, a 1st-year BCA Cyber Security student at Galgotias University, hands-on homelab builder, and cyber security intern at Cyber Secured India & SafeSkillz.

VOICE & TONE FOR X (TWITTER):
- 100% natural, authentic builder voice on #TechTwitter.
- Zero AI fluff, zero ChatGPT cliches ("dive deep", "game-changer", "without breaking a sweat", "delve").
- Direct, punchy, curiosity-inducing hooks.
- Real tech details: commands, tools, benchmarks, Linux internals, TryHackMe labs.

FORMAT RULES:
1. SINGLE TWEET FORMAT:
   - Output ONE standalone tweet strictly UNDER 270 characters (counting spaces and hashtags).
   - Structure: [Punchy hook / problem] + [Insight or fix] + [2 clean hashtags like #CyberSecurity #BuildInPublic #Homelab].

2. THREAD FORMAT (3 Tweets):
   - Output EXACTLY 3 tweets separated by the delimiter: "---TWEET---"
   - Each individual tweet MUST be strictly UNDER 270 characters.
   - Tweet 1: Hook, technical challenge, or assignment milestone + indicator (👇 or 🧵).
   - Tweet 2: The concrete 1-2-3 technical breakdown, tools, or commands.
   - Tweet 3: Real learning takeaway + peer discussion question + 2-3 hashtags.

CRITICAL: NEVER mention filenames (.docx) or say "As an AI". Output ONLY the tweet text.
"""

def generate_tweet(topic_data: dict, format_type: str = "single", angle_modifier: str = "") -> dict:
    """
    Generate either a single tweet (< 280 chars) or a 3-tweet thread.
    Returns: {
        "format": "single" | "thread",
        "tweets": [str, ...],
        "character_counts": [int, ...],
        "thesis": str
    }
    """
    topic = topic_data.get("topic", "Cyber Security & Homelab Engineering")
    category = topic_data.get("category", "")
    assignment_num = topic_data.get("assignment_num", "")
    source = topic_data.get("source", "")
    platform = topic_data.get("platform", "")
    context = topic_data.get("context", "")
    labs = topic_data.get("labs", [])
    
    is_assignment = bool(assignment_num) and ("intern" in str(context).lower() or source == "assignment")
    labs_str = "\n".join(labs) if labs else ""

    if format_type == "thread":
        format_instruction = "Generate a 3-tweet thread. Separate each tweet with '---TWEET---'. Every single tweet must be under 260 characters."
    else:
        format_instruction = "Generate a single punchy tweet strictly under 260 characters with 2 hashtags."

    if is_assignment:
        user_prompt = f"""Topic: Assignment-{assignment_num}: {topic}
Platform: {platform}
Lab Details: {labs_str}
Context: {context}
Internship: Cyber Secured India & SafeSkillz | Galgotias University

Task: {format_instruction}
{angle_modifier}"""
    else:
        user_prompt = f"""Topic: {topic}
Category: {category or 'Homelab & Systems Engineering'}
Platform: {platform}
Technical Context: {labs_str} {context}

Task: {format_instruction}
{angle_modifier}"""

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": TWITTER_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.65,
        "max_tokens": 500
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

    # Parse output
    if format_type == "thread" and "---TWEET---" in raw_output:
        raw_tweets = [t.strip() for t in raw_output.split("---TWEET---") if t.strip()]
    elif format_type == "thread":
        # Fallback split by double newline if model didn't use delimiter
        paragraphs = [p.strip() for p in raw_output.split("\n\n") if p.strip()]
        if len(paragraphs) >= 3:
            raw_tweets = paragraphs[:3]
        else:
            raw_tweets = [raw_output]
    else:
        raw_tweets = [raw_output]

    # Clean tweets & enforce length
    cleaned_tweets = []
    for t in raw_tweets:
        cleaned = re.sub(r'[\w\-]+\.docx', '', t).strip()
        cleaned = re.sub(r'^(Tweet \d+:|1\/3|2\/3|3\/3)\s*', '', cleaned, flags=re.IGNORECASE).strip()
        # Ensure under 280 chars
        if len(cleaned) > 275:
            # Trim gracefully at last sentence or word
            cleaned = cleaned[:272].rsplit(' ', 1)[0] + "..."
        cleaned_tweets.append(cleaned)

    first_tweet = cleaned_tweets[0] if cleaned_tweets else ""
    thesis = re.sub(r'^[🚀\s\-•*#]+', '', first_tweet)[:60].strip()

    return {
        "format": format_type,
        "tweets": cleaned_tweets,
        "character_counts": [len(t) for t in cleaned_tweets],
        "thesis": thesis
    }

def validate_tweets(tweets: list) -> tuple:
    """Validate character limits and banned words."""
    if not tweets:
        return False, "No tweets generated"
    for i, t in enumerate(tweets, 1):
        if len(t) < 20:
            return False, f"Tweet {i} is too short ({len(t)} chars)"
        if len(t) > 280:
            return False, f"Tweet {i} exceeds Twitter 280 limit ({len(t)} chars)"
        banned = [".docx", "as an ai", "chatgpt", "deepseek", "language model"]
        for b in banned:
            if b in t.lower():
                return False, f"Tweet {i} contains banned term '{b}'"
    return True, "Valid"

if __name__ == "__main__":
    test_topic = {
        "topic": "Linux Privilege Escalation & SUID Abuse",
        "assignment_num": "7",
        "source": "assignment",
        "platform": "TryHackMe",
        "context": "Basic Pentesting and Linux PrivEsc labs with SUID abuse and password cracking."
    }
    print("--- TESTING SINGLE TWEET ---")
    s_res = generate_tweet(test_topic, "single")
    for tw in s_res["tweets"]:
        print(f"[{len(tw)} chars] {tw}")

    print("\n--- TESTING THREAD ---")
    th_res = generate_tweet(test_topic, "thread")
    for i, tw in enumerate(th_res["tweets"], 1):
        print(f"[Tweet {i} | {len(tw)} chars]:\n{tw}\n")

