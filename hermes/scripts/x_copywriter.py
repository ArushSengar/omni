#!/usr/bin/env python3
"""
x_copywriter.py — High-Impact, Autonomous X (Twitter) Copywriting Engine for Arush Sengar.
Generates scroll-stopping, humanized tech content strictly adhering to Twitter limits (< 280 chars):
  - Format 1: Single Punchy Tweet (Hook + Technical insight + Targeted @mentions + 2 hashtags)
  - Format 2: 3-Tweet Mini Thread (Hook/Problem -> 1-2-3 Technical Fix -> Takeaway & Question)
"""

import os
import sys
import json
import re
import urllib.request
from pathlib import Path

# Smart Tagger
try:
    import smart_tagger
except ImportError:
    from hermes.scripts import smart_tagger

DEFAULT_URLS = [
    os.environ.get("OMNIROUTE_URL", "http://localhost:20128/v1"),
    "http://192.168.0.100:20128/v1"
]
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
DIRECTIVES_FILE = Path.home() / ".hermes" / "growth_manager_directives.json"

TWITTER_SYSTEM_PROMPT = """You are Arush Sengar, a 1st-year BCA Cyber Security student at Galgotias University, hands-on homelab builder, and cyber security intern at Cyber Secured India & SafeSkillz.

VOICE & TONE FOR X (TWITTER):
- 100% natural, authentic builder voice on #TechTwitter.
- Zero AI fluff, zero ChatGPT cliches ("dive deep", "game-changer", "without breaking a sweat", "delve").
- Direct, punchy, curiosity-inducing hooks.
- Real tech details: commands, tools, benchmarks, Linux internals, TryHackMe labs.

FORMAT RULES:
1. SINGLE TWEET FORMAT:
   - Output ONE standalone tweet strictly UNDER 260 characters (counting spaces and hashtags).
   - Structure: [Punchy hook / problem] + [Insight or fix with exact command] + [2 clean hashtags like #CyberSecurity #BuildInPublic #Linux].

2. THREAD FORMAT (3 Tweets):
   - Output EXACTLY 3 tweets separated by the delimiter: "---TWEET---"
   - Each individual tweet MUST be strictly UNDER 260 characters.
   - Tweet 1: Hook, technical challenge, or assignment milestone + indicator (👇 or 🧵).
   - Tweet 2: The concrete 1-2-3 technical breakdown, tools, or commands.
   - Tweet 3: Real learning takeaway + peer discussion question + 2-3 hashtags.

ANTI-AI & CLEANLINESS RULES (MANDATORY):
- NEVER output conversational preambles ("Here is your tweet:", "Certainly!", "Sure!").
- DO NOT use markdown bold asterisks (**) or markdown backticks (`). X does not render markdown. Write commands as plain text or in single quotes.
- NEVER mention filenames (.docx) or say "As an AI". Output ONLY the tweet text.
"""


def call_llm(messages: list, max_tokens: int = 400, temperature: float = 0.65) -> str:
    payload = {
        "model": MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    data_bytes = json.dumps(payload).encode("utf-8")

    last_err = None
    for url in DEFAULT_URLS:
        try:
            req = urllib.request.Request(
                f"{url}/chat/completions",
                data=data_bytes,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {API_KEY}"
                }
            )
            with urllib.request.urlopen(req, timeout=45) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                return res["choices"][0]["message"]["content"].strip()
        except Exception as e:
            last_err = e
            continue

    raise RuntimeError(f"Failed to connect to OmniRoute LLM at {DEFAULT_URLS}: {last_err}")


def sanitize_tweet_text(text: str) -> str:
    """Strips conversational preambles, fences, and raw markdown from tweets."""
    if not text:
        return ""
    text = re.sub(r'^```(?:markdown)?\s*\n', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\n```\s*$', '', text)

    # Strip conversational lead-ins
    lines = text.splitlines()
    cleaned = []
    started = False
    conversational = [
        r"^here(?:['’]?s|\s+is|\s+are)\b",
        r"^certainly\b",
        r"^sure\b",
        r"^below is\b",
        r"^tweet\s*\d*:\s*",
        r"^post\s*:\s*",
        r"^single tweet\s*:\s*",
        r"^thread\s*:\s*",
        r".*as arush sengar.*",
        r".*here(?:['’]?s|\s+is)\s+(?:your\s+)?tweet.*",
        r"^title\s*:",
        r"^headline\s*:",
    ]
    for l in lines:
        st = l.strip()
        if not started:
            if not st:
                continue
            if any(re.match(p, st.lower()) for p in conversational):
                continue
            started = True
        cleaned.append(l)

    text = "\n".join(cleaned).strip()
    # Strip surrounding quotes
    text = re.sub(r'^["\']|["\']$', '', text).strip()
    # Strip raw markdown asterisks and backticks
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    text = text.replace('**', '')
    text = re.sub(r'`([^`]+)`', r'\1', text)
    text = text.replace('`', '')
    text = re.sub(r'[\w\-]+\.docx', '', text)
    return text.strip()


def validate_tweets(tweets: list) -> tuple:
    """Validates generated tweet(s) against length and anti-AI constraints."""
    if not tweets or not isinstance(tweets, list):
        return False, "No tweets provided"

    banned = [
        ".docx", "as an ai", "i am an ai", "chatgpt", "deepseek",
        "language model", "without breaking a sweat", "dive deep",
        "delve", "game-changer", "here is your", "here's your",
        "certainly!", "sure!", "as arush sengar"
    ]

    for i, tw in enumerate(tweets, 1):
        clean_tw = tw.strip()
        if not clean_tw:
            return False, f"Tweet {i} is empty"
        if len(clean_tw) > 280:
            return False, f"Tweet {i} exceeds 280 characters ({len(clean_tw)} chars)"
        lower_tw = clean_tw.lower()
        for b in banned:
            if b in lower_tw:
                return False, f"Tweet {i} contains forbidden term: '{b}'"
        if "**" in clean_tw:
            return False, f"Tweet {i} contains raw markdown asterisks (**)"
        if "`" in clean_tw:
            return False, f"Tweet {i} contains raw markdown backticks (`)"
        if "---" in clean_tw and "---tweet---" not in clean_tw.lower():
            return False, f"Tweet {i} contains raw horizontal divider lines"

    # Verify hashtags present in thread or single tweet
    if not any("#" in tw for tw in tweets):
        return False, "Tweets missing hashtags"

    return True, "Valid"


def generate_tweet(topic_data: dict, format_type: str = "single", angle_modifier: str = "") -> dict:
    topic = topic_data.get("topic", "Cyber Security & Homelab Engineering")
    category = topic_data.get("category", "")
    assignment_num = topic_data.get("assignment_num", "")
    source = topic_data.get("source", "")
    platform = topic_data.get("platform", "")
    context = topic_data.get("context", "")
    labs = topic_data.get("labs", [])

    is_assignment = bool(assignment_num) or source == "assignment"
    labs_str = "\n".join(labs) if labs else ""

    if format_type == "thread":
        format_instruction = "Generate a 3-tweet thread. Separate each tweet with '---TWEET---'. Every single tweet must be under 250 characters."
    else:
        format_instruction = "Generate a single punchy tweet strictly under 250 characters with 2 hashtags."

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

    messages = [
        {"role": "system", "content": TWITTER_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt}
    ]

    raw_output = call_llm(messages, max_tokens=400, temperature=0.65)

    if format_type == "thread" and "---TWEET---" in raw_output:
        raw_tweets = [sanitize_tweet_text(t) for t in raw_output.split("---TWEET---") if t.strip()]
        tweets = [smart_tagger.inject_tags_into_tweet(t, topic_data) if i == 0 else t for i, t in enumerate(raw_tweets)]
        tweets = [sanitize_tweet_text(t) for t in tweets]
    else:
        cleaned_tweet = sanitize_tweet_text(raw_output)
        tagged_tweet = smart_tagger.inject_tags_into_tweet(cleaned_tweet, topic_data)
        tweets = [sanitize_tweet_text(tagged_tweet)]

    counts = [len(t) for t in tweets]
    thesis = tweets[0][:50] if tweets else topic[:50]

    return {
        "format": format_type,
        "tweets": tweets,
        "character_counts": counts,
        "thesis": thesis
    }


if __name__ == "__main__":
    sample = {
        "topic": "Linux Privilege Escalation via SUID",
        "assignment_num": "7",
        "source": "assignment",
        "platform": "TryHackMe",
        "context": "Escalated shell using find command SUID bit.",
        "labs": ["TryHackMe"]
    }
    res = generate_tweet(sample, "single")
    print("Tweet:", res["tweets"][0])
    print("Chars:", res["character_counts"][0])
