#!/usr/bin/env python3
"""
x_daily_post.py — Autonomous, 100% Free X (Twitter) Engine for Arush Sengar.
Designed for 1st-year student builder, homelab engineer, and cyber security intern.

Key Features:
  1. DETECT   — Scans completed TryHackMe/OWASP assignments or 10-domain builder backlogs.
  2. COMPOSE  — OmniRoute LLM writes scroll-stopping, authentic tech copy (< 280 chars per tweet).
                Supports both Single Punchy Tweet and 3-Tweet Mini-Threads.
  3. VISUAL   — Generates branded 1200x1200 proof-of-work collage (real lab proof) or
                dynamic dark-mode terminal cards tailored to the topic domain. Zero AI stock art.
  4. PUBLISH  — 100% FREE Headless Playwright Browser Publisher (~/.twitter-profile).
                Zero official API costs, zero subscriptions ($0.00 forever).
                Supports Composio CLI as optional fallback.
  5. ARCHIVE  — Saves tweet JSON to ~/posts/x/ and logs history to ~/.hermes/x_daily/daily_tweets.json.

Usage:
  python3 ~/x_daily_post.py                 # Full auto run (single tweet)
  python3 ~/x_daily_post.py --thread        # Full auto run (3-tweet thread)
  python3 ~/x_daily_post.py --dry-run       # Compose & render without publishing
  python3 ~/x_daily_post.py --assignment 7  # Force specific assignment
  python3 ~/x_daily_post.py --topic "X"     # Force custom topic
"""

import os
import sys
# Strip stale python3.14 paths only when running under python < 3.14
if sys.version_info < (3, 14):
    sys.path = [p for p in sys.path if "python3.14" not in p]
sys.path.insert(0, "/home/arush")

import argparse
import json
import subprocess
import time
from datetime import datetime
from pathlib import Path

# Core modules
import linkedin_activity_detector
import linkedin_collage_generator
import x_copywriter

STATE_DIR = Path.home() / ".hermes" / "x_daily"
STATE_DIR.mkdir(parents=True, exist_ok=True)
USED_FILE = STATE_DIR / "used.json"
HISTORY_FILE = STATE_DIR / "daily_tweets.json"

ARCHIVE_DIR = Path.home() / "posts" / "x"
ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

PLAYWRIGHT_CANDIDATES = [
    "/home/arush/.hermes/venv/bin/python",
    "/home/arush/.hermes/installs/c4e5f05fc62c46c7/environments/c3eca3e27a664bb2929bbedfcbc483b7/venv/bin/python",
]
PLAYWRIGHT_PYTHON = next((p for p in PLAYWRIGHT_CANDIDATES if os.path.exists(p)), sys.executable)
COOKIE_FILE = Path.home() / ".twitter-profile" / "cookies.json"


def publish_playwright_free(tweets: list, img_path: str = "") -> bool:
    """100% Free Headless Playwright Publisher (No Paid APIs)."""
    print("[4] Publishing via 100% Free Playwright Headless Browser...")
    cmd = [
        PLAYWRIGHT_PYTHON if os.path.exists(PLAYWRIGHT_PYTHON) else sys.executable,
        "/home/arush/x_autopost.py"
    ]
    if img_path and os.path.exists(img_path):
        cmd.extend(["--image", str(img_path)])
    if len(tweets) > 1:
        cmd.append("--thread")
    cmd.extend(tweets)

    r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    print(r.stdout)
    if r.stderr:
        print(r.stderr)
    return r.returncode == 0


def publish_composio_fallback(tweets: list, img_path: str = "") -> list:
    """Optional Composio fallback if account linked."""
    print("[4-Fallback] Attempting Composio publish...")
    # Basic single tweet via composio
    ts_script = f"""
    const res = await execute("TWITTER_CREATION_OF_A_POST", {{ text: {json.dumps(tweets[0])} }});
    if (!res.successful) throw new Error(res.error || "Failed");
    console.log("POST_ID:" + (res.data?.id || "ok"));
    """
    cmd = ["/home/arush/.local/bin/composio", "run", ts_script]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    for line in r.stdout.splitlines():
        if "POST_ID:" in line:
            return [line.split("POST_ID:", 1)[1].strip()]
    raise RuntimeError(r.stderr or r.stdout)


def publish(tweets: list, img_path: str = "") -> list:
    """Publish to Twitter using the 100% Free Playwright engine first."""
    tweets = [x_copywriter.sanitize_tweet_text(t) for t in tweets if x_copywriter.sanitize_tweet_text(t)]
    # Check if cookies exist
    if not COOKIE_FILE.exists():
        print("\n" + "=" * 55)
        print("💡 100% FREE TWITTER/X SETUP REQUIRED (NO PAID API)")
        print("=" * 55)
        print("Aapko Twitter ka koi $100-$200 paid API plan nahi lena hai!")
        print("Bas apne browser se 2 free cookies copy karke yeh command run karein:")
        print("  python3 ~/x_setup_cookies.py --auth-token \"<TOKEN>\" --ct0 \"<CT0>\"")
        print("=" * 55 + "\n")
        raise ConnectionError("Twitter cookies missing. Run x_setup_cookies.py to setup free session.")

    ok = publish_playwright_free(tweets, img_path)
    if ok:
        return ["free-playwright-published"]
    
    # Try composio fallback if playwright hit an issue
    print("[warn] Free Playwright run failed, checking Composio fallback...")
    try:
        return publish_composio_fallback(tweets, img_path)
    except Exception as e:
        raise RuntimeError(f"Playwright failed and Composio failed ({e})")


def log_tweet(topic_data: dict, tweets: list, thesis: str, img_path: str, tweet_ids: list):
    """Log the published tweet/thread to daily_tweets.json and state."""
    history = []
    if HISTORY_FILE.exists():
        try:
            history = json.loads(HISTORY_FILE.read_text())
        except Exception:
            history = []

    first_id = tweet_ids[0] if tweet_ids else ""
    tweet_url = f"https://x.com/i/web/status/{first_id}" if first_id and first_id not in ["ok", "free-playwright-published"] else ""

    record = {
        "timestamp": datetime.now().isoformat(),
        "topic": topic_data.get("topic"),
        "assignment_num": topic_data.get("assignment_num", ""),
        "source": topic_data.get("source"),
        "thesis": thesis,
        "format": "thread" if len(tweets) > 1 else "single",
        "tweets": tweets,
        "img_path": str(img_path) if img_path else "",
        "tweet_ids": tweet_ids,
        "url": tweet_url
    }
    history.append(record)
    HISTORY_FILE.write_text(json.dumps(history, indent=2))

    used = []
    if USED_FILE.exists():
        try:
            used = json.loads(USED_FILE.read_text())
        except Exception:
            used = []
    t_name = topic_data.get("topic", "")
    if t_name and t_name not in used:
        used.append(t_name)
        USED_FILE.write_text(json.dumps(used, indent=2))


def archive_post(topic_data: dict, tweets: list, img_path: str, tweet_ids: list):
    """Save clean markdown archive to ~/posts/x/."""
    dt_str = datetime.now().strftime("%Y%m%d_%H%M")
    safe_topic = "".join(c for c in topic_data.get("topic", "tweet") if c.isalnum() or c in " _-")[:30].strip()
    archive_file = ARCHIVE_DIR / f"{dt_str}_{safe_topic}.md"

    md_content = f"""# X (Twitter) Post: {topic_data.get('topic')}
**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M IST')}  
**Assignment:** {topic_data.get('assignment_num') or 'Autonomous Builder'}  
**Format:** {'Thread (' + str(len(tweets)) + ' tweets)' if len(tweets) > 1 else 'Single Tweet'}  
**Engine:** 100% Free Headless Playwright  
**Image:** `{img_path}`  
**Status:** {tweet_ids}  

---

"""
    for i, tw in enumerate(tweets, 1):
        md_content += f"### Tweet {i} ({len(tw)} chars)\n```\n{tw}\n```\n\n"

    archive_file.write_text(md_content)
    print(f"[5] Archived to: {archive_file}")


def main():
    parser = argparse.ArgumentParser(description="Autonomous 100% Free X (Twitter) Engine for Arush Sengar")
    parser.add_argument("--dry-run", action="store_true", help="Generate copy & visual without publishing")
    parser.add_argument("--preview", action="store_true", help="Preview copy and visual path only")
    parser.add_argument("--thread", action="store_true", help="Generate as a 3-tweet thread")
    parser.add_argument("--single", action="store_true", help="Generate as a single punchy tweet (default)")
    parser.add_argument("--assignment", type=int, help="Force specific assignment number")
    parser.add_argument("--topic", type=str, help="Force custom topic string")
    parser.add_argument("--image", type=str, help="Path to custom image")
    args = parser.parse_args()

    format_type = "thread" if args.thread else "single"

    print("=" * 55)
    print("      AUTONOMOUS X (TWITTER) ENGINE (100% FREE)   ")
    print("=" * 55)

    # 1. Activity / Topic Detection
    print("[1] Inspecting activities & assignments...")
    topic_data = linkedin_activity_detector.detect_daily_topic(
        force_assignment=args.assignment,
        force_topic=args.topic
    )

    if not topic_data:
        print("[SKIP] No new activity or pending assignment found today.")
        sys.exit(0)

    print(f"    Topic Selected : {topic_data.get('topic')}")
    print(f"    Assignment #   : {topic_data.get('assignment_num') or 'N/A'}")
    print(f"    Platform       : {topic_data.get('platform')}")
    print(f"    Screenshots    : {len(topic_data.get('images', []))} available")
    print(f"    Format         : {format_type.upper()}")

    # 2. X Copywriting
    print(f"\n[2] Composing {format_type} tweet with OmniRoute...")
    tweet_result = x_copywriter.generate_tweet(topic_data, format_type=format_type)
    tweets = tweet_result["tweets"]
    thesis = tweet_result["thesis"]

    # Validate
    valid, reason = x_copywriter.validate_tweets(tweets)
    if not valid:
        print(f"    [warn] First attempt invalid: {reason}. Retrying with strict modifier...")
        tweet_result = x_copywriter.generate_tweet(topic_data, format_type=format_type, angle_modifier="STRICT: Be concise, strictly under 250 characters.")
        tweets = tweet_result["tweets"]

    print("\n---------------- GENERATED TWEET(S) ----------------")
    for i, tw in enumerate(tweets, 1):
        print(f"[{i}/{len(tweets)}] ({len(tw)} chars):\n{tw}\n")
    print("----------------------------------------------------")
    print(f"Thesis Hook : {thesis}")

    # 3. Visual Generation
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    if args.image and os.path.exists(args.image):
        img_path = str(args.image)
        print(f"\n[3] Using explicit user image: {img_path}")
    else:
        out_visual = ARCHIVE_DIR / f"{timestamp}_visual.png"
        print(f"\n[3] Generating visual (Proof Collage / Terminal Proof Card)...")
        try:
            linkedin_collage_generator.render_collage(topic_data, str(out_visual))
            img_path = str(out_visual)
            print(f"    Visual generated: {img_path} ({os.path.getsize(img_path)} bytes)")
        except Exception as e:
            print(f"    Visual generation error: {e}")
            img_path = ""

    # Dry-run / Preview
    if args.dry_run or args.preview:
        print("\n[DRY-RUN / PREVIEW] Skipping Twitter publication.")
        archive_post(topic_data, tweets, img_path, ["dry-run-preview"])
        print("\n✅ System test successful! Everything is generated and validated.")
        return

    # 4. Publication (100% Free Playwright)
    print("\n[4] Publishing to Twitter/X...")
    try:
        tweet_ids = publish(tweets, img_path)
        print(f"\n🚀 Successfully published to X via Free Method! Status: {tweet_ids}")
    except ConnectionError as ce:
        print(f"\n⚠️  {ce}")
        archive_post(topic_data, tweets, img_path, ["cookies-setup-needed"])
        return
    except Exception as e:
        print(f"\n❌ Publication failed: {e}")
        archive_post(topic_data, tweets, img_path, ["failed"])
        raise

    # 5. Archive & Log
    archive_post(topic_data, tweets, img_path, tweet_ids)
    log_tweet(topic_data, tweets, thesis, img_path, tweet_ids)
    print("\n✅ Autonomous X Posting Pipeline Completed Successfully.")


if __name__ == "__main__":
    main()
