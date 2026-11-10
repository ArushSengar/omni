#!/usr/bin/env python3
"""
linkedin_copywriter.py — Generates humanized, high-credibility LinkedIn posts for Arush Sengar.
Enforces authentic 1st-year student builder voice, context-aware company @tagging,
and SEO keyword optimization. Zero robotic AI slop.

Content Pillars:
  Pillar 1: Hands-On Lab / Assignment Breakdown (TryHackMe, OWASP, Pentesting)
  Pillar 2: Real-World Student Homelab & Hardware (Raspberry Pi 4 4GB, Linux Kernel, Docker)
  Pillar 3: Breaking AI & Tech Research/News (DeepSeek/Llama architecture, zero-days, CVE analysis)
"""

import os
import sys
import json
import re
import urllib.request
import urllib.error
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

SYSTEM_PROMPT = """You are Arush Sengar, a 1st-year BCA Cyber Security student at Galgotias University, homelab tinkerer running a 24/7 Raspberry Pi 4 cluster, and intern at Cyber Secured India & SafeSkillz.

VOICE & TONE GUIDELINES (MANDATORY 100% HUMAN STUDENT BUILDER):
- Sound like an actual 19-year-old student builder sharing practical experiments, mistakes, and breakthroughs.
- Write with candid curiosity: "College lectures teach dry definitions, but running it on actual hardware hits completely different."
- NEVER sound like an AI marketing bot, corporate PR manager, or textbook.

BANNED AI CLICHÉS (DO NOT USE UNDER ANY CIRCUMSTANCES):
* NO opening rocket emojis (🚀) or emojis on every bullet point.
* NO bullet points starting with diamond or flame emojis (🔹, 💡, 🔥).
* NO ChatGPT filler phrases: "in today's fast-paced digital world", "without breaking a sweat", "rock-solid", "delve", "testament to", "game-changer", "dive deep", "seamlessly", "harnessing", "unlock", "crucial role", "pivotal", "fascinating journey".

ANTI-AI & FORMATTING RULES (STRICTLY MANDATORY):
* Output ONLY the raw post content. NEVER include conversational preambles or greetings like "Here's your LinkedIn post as Arush Sengar:", "Here is the post:", "Certainly!", "Sure!", "Draft:", "Title:", "Headline:".
* NEVER output horizontal divider lines like "---" or "===". Start IMMEDIATELY on line 1 with the opening hook.
* DO NOT USE MARKDOWN ASTERISKS (**) OR BACKTICKS (`) ANYWHERE. LinkedIn does not render markdown; it displays raw asterisks and backticks as ugly clutter. Write headings and commands cleanly as plain text or standard capitalization (e.g. 'Student Takeaway:' or 'STUDENT TAKEAWAY:').

POST STRUCTURE:
1. Scroll-Stopping Hook (Line 1-2):
   - Start with real technical friction, a surprising failure, or a counter-intuitive observation.
   - Front-load primary keywords for LinkedIn search SEO (e.g. Linux Privilege Escalation, eBPF Telemetry, Raspberry Pi 4 Homelab).
2. The Friction / Diagnosis (Why it matters):
   - What broke or what did the default setup fail to handle under the hood.
3. The Concrete Fix / Walkthrough:
   - Formatted as a clean, scannable numbered list (1, 2, 3) with exact commands, configs, or tools.
4. The Measurable Impact:
   - What was the actual outcome (e.g., memory saved, latency dropped, root shell obtained, zero false positives).
5. Student Takeaway:
   - A candid reflection on what breaking and building taught you.
6. Engaging Debate Question:
   - A specific, thought-provoking question for fellow engineers and students (not a generic "What do you think?").
7. Targeted SEO Hashtags (5-6 tags matching the domain).

LENGTH:
- Strictly between 140 and 210 words. Punchy, clean line breaks, zero fluff.
"""


def call_llm(messages: list, max_tokens: int = 850, temperature: float = 0.65) -> str:
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


def load_growth_directives() -> str:
    """Loads active tuning directives from the Growth Manager."""
    if DIRECTIVES_FILE.exists():
        try:
            data = json.loads(DIRECTIVES_FILE.read_text(encoding="utf-8"))
            recs = data.get("recommendations", [])
            if recs:
                return "\nGROWTH MANAGER TUNING DIRECTIVES:\n- " + "\n- ".join(recs)
        except Exception:
            pass
    return ""


def sanitize_human_post(text: str) -> str:
    """
    Strips robotic LLM conversational preambles, horizontal separators,
    raw markdown asterisks/backticks, and trailing conversational sign-offs.
    Ensures the post appears 100% human-crafted on LinkedIn.
    """
    if not text:
        return ""

    # Strip code block fences if the LLM wrapped the whole response
    text = re.sub(r'^```(?:markdown)?\s*\n', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\n```\s*$', '', text)

    lines = text.splitlines()
    cleaned_lines = []
    post_started = False

    # Regex patterns for conversational opener lines
    conversational_patterns = [
        r"^here(?:['’]?s|\s+is|\s+are)\b",
        r"^certainly\b",
        r"^sure\b",
        r"^below is\b",
        r"^draft\s*:",
        r"^post\s*:",
        r"^linkedin post\b",
        r".*as arush sengar.*",
        r".*here(?:['’]?s|\s+is)\s+(?:your\s+)?linkedin\s+post.*",
        r"^as arush sengar\b",
        r"^here is your post\b",
        r"^title\s*:",
        r"^headline\s*:",
    ]

    for line in lines:
        stripped = line.strip()

        # If we haven't found the actual post start yet:
        if not post_started:
            if not stripped:
                continue
            # Skip divider lines like ---, ===, ***, ___
            if re.match(r"^[-=_*~]{3,}$", stripped):
                continue
            # Skip conversational introductions
            lower = stripped.lower()
            if any(re.match(p, lower) for p in conversational_patterns):
                continue
            # If it passed these, this is the first real line of the post
            post_started = True

        # If post already started, filter out horizontal rules (e.g. ---)
        if re.match(r"^[-=_*~]{3,}$", stripped):
            continue

        # Check for conversational trailing sign-offs
        lower = stripped.lower()
        if any(lower.startswith(p) for p in [
            "hope this helps", "let me know if", "feel free to modify", "feel free to tweak"
        ]):
            break

        cleaned_lines.append(line)

    text = "\n".join(cleaned_lines).strip()

    # Clean raw markdown asterisks (LinkedIn does not render **bold**)
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    text = text.replace('**', '')

    # Clean raw backticks (LinkedIn does not render `code`)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    text = text.replace('`', '')

    # Clean markdown headers (# Header)
    text = re.sub(r'^[#]+\s*', '', text, flags=re.MULTILINE)

    # Clean any leftover standalone artifacts or docx references
    text = re.sub(r'[\w\-]+\.docx', '', text)

    return text.strip()


def generate_post(topic_data: dict, angle_modifier: str = "") -> tuple:
    topic = topic_data.get("topic", "Cyber Security Engineering")
    category = topic_data.get("category", "")
    assignment_num = topic_data.get("assignment_num", "")
    source = topic_data.get("source", "")
    platform = topic_data.get("platform", "")
    context = topic_data.get("context", "")
    labs = topic_data.get("labs", [])

    is_assignment = bool(assignment_num) or source == "assignment"
    labs_str = "\n".join(labs) if labs else ""
    directives = load_growth_directives()

    if is_assignment:
        user_prompt = f"""Write an authentic, human LinkedIn post as Arush Sengar about:
Topic: {topic}
Assignment Number: {assignment_num}
Lab / Platform: {platform}
Lab Details & Context:
{labs_str}
{context}

{angle_modifier}
{directives}

Requirements:
- Sound like a real student sharing an actual lab milestone.
- Explain the real escalation or exploit vector clearly.
- Output ONLY the final LinkedIn post. Zero preambles, zero dividers (---), zero markdown asterisks."""
    else:
        user_prompt = f"""Write an authentic, human LinkedIn post as Arush Sengar about:
Topic: {topic}
Category: {category or 'Engineering & Homelab'}
Platform/Environment: {platform}
Technical Context:
{labs_str}
{context}

{angle_modifier}
{directives}

Requirements:
- Candid student builder voice (Raspberry Pi 4 / homelab / cyber security student).
- Numbered breakdown (1, 2, 3) of the actual fix or discovery.
- Output ONLY the final LinkedIn post. Zero preambles, zero dividers (---), zero markdown asterisks."""

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt}
    ]

    raw_output = call_llm(messages, max_tokens=850, temperature=0.65)

    # Strict anti-AI & anti-preamble sanitization
    clean_post = sanitize_human_post(raw_output)

    # Apply Context-Aware Smart Tagging
    tagged_post = smart_tagger.inject_tags_into_linkedin(clean_post, topic_data)

    # Second pass sanitize to guarantee clean plain text
    tagged_post = sanitize_human_post(tagged_post)

    first_line = tagged_post.split("\n")[0].strip()
    thesis = re.sub(r'^[🚀\s\-•*#]+', '', first_line)[:60].strip()

    return tagged_post, thesis, ""


def validate_post(post: str) -> tuple:
    if not post:
        return False, "Post is empty"
    words = post.split()
    if len(words) < 50:
        return False, f"Post too short ({len(words)} words)"
    if len(words) > 280:
        return False, f"Post too long ({len(words)} words, max 280)"

    lower_post = post.lower()
    for forbidden in [
        "here's your", "here is your", "here's a", "here is a",
        "certainly", "sure,", "sure!", "draft:", "below is",
        "title:", "as arush sengar", "linkedin post:"
    ]:
        if forbidden in lower_post[:120]:
            return False, f"Post starts with conversational AI preamble: contains '{forbidden}'"

    if "---" in post or "===" in post:
        return False, "Post contains raw divider lines"

    if "**" in post:
        return False, "Post contains raw markdown asterisks (**)"

    if "`" in post:
        return False, "Post contains raw markdown backticks (`)"

    banned = [".docx", "as an ai", "i am an ai", "chatgpt", "deepseek", "language model", "without breaking a sweat", "game-changer"]
    for b in banned:
        if b in lower_post:
            return False, f"Post contains forbidden term: '{b}'"
    if "#" not in post:
        return False, "Post missing hashtags"
    return True, "Valid"


if __name__ == "__main__":
    test_topic = {
        "topic": "Tuning Linux Dirty Memory Pages to Stop Raspberry Pi I/O Freezes",
        "assignment_num": "",
        "source": "autonomous_research",
        "platform": "Raspberry Pi 4",
        "context": "Pi 4 system frozen during heavy multi-model LLM routing. The page cache accumulated dirty memory up to 20% of system RAM before flusher threads woke up, causing latency spikes of 4500ms. Tuned vm.dirty_background_ratio to 5% and vm.dirty_ratio to 10% in /etc/sysctl.conf.",
        "labs": ["sysctl", "vmstat", "vmtouch"],
        "tags": ["Linux", "Kernel", "Homelab", "RaspberryPi"]
    }
    p, th, _ = generate_post(test_topic)
    print("=== DRAFT WITH SMART TAGS ===")
    print(p)
