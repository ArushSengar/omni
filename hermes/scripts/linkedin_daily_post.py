#!/home/arush/.hermes/venv/bin/python
"""
linkedin_daily_post.py — Autonomous, Humanized LinkedIn Engine for Arush Sengar.
Built to match and exceed the top-performing peer benchmark (Kaushik Choubey formula):
  1. DETECT   — Scans actual completed assignments (DOCX in /home/arush/assignments_archive/documents),
                extracted lab evidence images, homelab metrics, or notes.
  2. COMPOSE  — OmniRoute LLM writes in authentic student voice:
                (Milestone greeting -> hands-on lab breakdown -> 3 punchy takeaways ->
                 gratitude to Cyber Secured India, SafeSkillz & Galgotias University -> community question -> SEO hashtags).
  3. VISUAL   — Generates branded 1200x1200 quad proof-of-work collage using real lab screenshots,
                or generates high-impact 3D AI cyber art via OmniRoute (antigravity/gemini-3.1-flash-image)
                with Pollinations.ai (FLUX) and live terminal fallbacks. Zero generic stock photos.
  4. PUBLISH  — Posts via Composio CLI LINKEDIN_CREATE_LINKED_IN_POST with attached image.
  5. ARCHIVE  — Saves post markdown to ~/posts/daily/ and records state to daily_learnings.json.

Usage:
  python3 ~/linkedin_daily_post.py                   # Full auto daily run
  python3 ~/linkedin_daily_post.py --dry-run         # Compose, generate visual, and validate without publishing
  python3 ~/linkedin_daily_post.py --assignment 7    # Force specific assignment number
  python3 ~/linkedin_daily_post.py --topic "X"       # Force custom topic
  python3 ~/linkedin_daily_post.py --preview         # Generate & print preview
"""

import os
import sys
# Strip stale python3.14 paths
sys.path = [p for p in sys.path if "python3.14" not in p]
sys.path.insert(0, "/home/arush")

import argparse
import json
import subprocess
import time
from datetime import datetime
from pathlib import Path

# Import our upgraded modules
import linkedin_activity_detector
import linkedin_copywriter
import linkedin_collage_generator

STATE_DIR = Path.home() / ".hermes" / "linkedin_daily"
STATE_DIR.mkdir(parents=True, exist_ok=True)
USED_FILE = STATE_DIR / "used.json"
LEARNINGS_FILE = STATE_DIR / "daily_learnings.json"

ARCHIVE_DIR = Path.home() / "posts" / "daily"
ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

AUTHOR_URN = "urn:li:person:qzJKgZnzTh"


def publish_composio(post_text: str, img_path: str = "") -> str:
    """Publish to LinkedIn using Composio CLI with optional image."""
    images_arg = f', images: [{json.dumps(str(img_path))}]' if img_path and os.path.exists(img_path) else ''
    cmd = [
        "/home/arush/.local/bin/composio", "run", f"""
        const res = await execute("LINKEDIN_CREATE_LINKED_IN_POST", {{
            author: "{AUTHOR_URN}",
            commentary: {json.dumps(post_text)}{images_arg}
        }});
        if (!res.successful) throw new Error(res.error || "Publish failed");
        console.log("PUBLISHED_SHARE_URN:" + (res.data?.x_restli_id || "ok"));
        """
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    for line in r.stdout.splitlines():
        if "PUBLISHED_SHARE_URN:" in line:
            return line.split(":", 1)[1].strip()
    raise RuntimeError(f"Composio publish failed: {r.stderr or r.stdout}")


def publish(post: str, img_path: str) -> str:
    """Publish via Composio with Playwright fallback."""
    try:
        print("[4] Publishing via Composio CLI...")
        return publish_composio(post, img_path)
    except Exception as e:
        print(f"[warn] Composio failed ({e}), falling back to Playwright...")
        r = subprocess.run(
            ["/home/arush/.hermes/venv/bin/python", "/home/arush/linkedin_autopost.py", post, str(img_path)],
            capture_output=True, text=True, timeout=120
        )
        for line in r.stdout.splitlines():
            if "PUBLISHED_SHARE_URN:" in line:
                return line.split(":", 1)[1].strip()
        raise RuntimeError(f"Playwright also failed: {r.stderr or r.stdout}")


def log_learning(topic_data: dict, post: str, thesis: str, img_path: str, share_urn: str):
    """Log the published post to daily_learnings.json and update topic history."""
    learnings = []
    if LEARNINGS_FILE.exists():
        try:
            learnings = json.loads(LEARNINGS_FILE.read_text())
        except Exception:
            learnings = []

    record = {
        "timestamp": datetime.now().isoformat(),
        "topic": topic_data.get("topic"),
        "assignment_num": topic_data.get("assignment_num", ""),
        "source": topic_data.get("source"),
        "thesis": thesis,
        "post": post,
        "img_path": str(img_path) if img_path else "",
        "share_urn": share_urn,
        "url": f"https://www.linkedin.com/feed/update/{share_urn}/" if "urn:li:" in share_urn else ""
    }
    learnings.append(record)
    LEARNINGS_FILE.write_text(json.dumps(learnings, indent=2))

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


def main():
    parser = argparse.ArgumentParser(description="Autonomous LinkedIn Poster for Arush Sengar")
    parser.add_argument("--dry-run", action="store_true", help="Generate post & visual without publishing")
    parser.add_argument("--preview", action="store_true", help="Print post & generate image preview")
    parser.add_argument("--assignment", help="Force specific assignment number (e.g. 6, 7, 10, 11, 12)")
    parser.add_argument("--topic", help="Force specific topic name")
    parser.add_argument("--image", help="Use specific image instead of generating collage")
    args = parser.parse_args()

    print("==================================================")
    print("  AUTONOMOUS LINKEDIN POSTING ENGINE (GOD-MODE)   ")
    print("==================================================")

    # 1. Detect activity & select topic
    print("[1] Inspecting activities & assignments...")
    topic_data = linkedin_activity_detector.detect_daily_topic(
        force_assignment=args.assignment,
        force_topic=args.topic
    )

    if not topic_data:
        print("[SKIP] No new activity or pending assignment found today.")
        sys.exit(0)

    print(f"    Topic Selected : {topic_data.get('topic')}")
    print(f"    Category       : {topic_data.get('category', 'N/A')}")
    print(f"    Assignment #   : {topic_data.get('assignment_num', 'N/A')}")
    print(f"    Platform       : {topic_data.get('platform', 'Hands-on Lab')}")
    print(f"    Source         : {topic_data.get('source')}")
    print(f"    Screenshots    : {len(topic_data.get('images', []))} available")

    # 2. Compose humanized copy
    print("\n[2] Composing humanized LinkedIn post with OmniRoute...")
    post = thesis = img_prompt = None
    for attempt in range(3):
        angle = "" if attempt == 0 else (
            "Focus deeply on the specific commands and technical hurdles encountered." if attempt == 1 else
            "Focus on practical lessons learned and advice for fellow BCA cybersecurity students."
        )
        try:
            post, thesis, img_prompt = linkedin_copywriter.generate_post(topic_data, angle_modifier=angle)
            ok, why = linkedin_copywriter.validate_post(post)
            if ok:
                print(f"    Attempt {attempt + 1}: Valid ({len(post.split())} words)")
                break
            print(f"    Attempt {attempt + 1} rejected ({why}), retrying...")
            post = thesis = img_prompt = None
        except Exception as e:
            print(f"    Attempt {attempt + 1} error: {e}")
            time.sleep(2)

    if not post:
        sys.exit("Failed to generate a valid post after 3 attempts.")

    topic_data["image_prompt"] = img_prompt or ""

    print("\n---------------- GENERATED POST ----------------")
    print(post)
    print("------------------------------------------------")
    print(f"Thesis Hook : {thesis}")
    if img_prompt:
        print(f"AI Prompt   : {img_prompt}")

    # 3. Generate Visual (Proof-of-Work Collage or AI Concept Art)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    img_path = None

    if args.image and os.path.exists(args.image):
        img_path = Path(args.image)
        print(f"\n[3] Using explicit user image: {img_path}")
    else:
        out_visual = ARCHIVE_DIR / f"{timestamp}_visual.png"
        print(f"\n[3] Generating visual (Proof Collage / AI 3D Cyber Art)...")
        try:
            linkedin_collage_generator.render_collage(topic_data, str(out_visual))
            img_path = out_visual
            print(f"    Visual generated: {img_path} ({os.path.getsize(img_path)} bytes)")
        except Exception as e:
            print(f"    Visual generation error: {e}")
            img_path = None

    if args.dry_run or args.preview:
        print("\n[DRY-RUN / PREVIEW] Skipping LinkedIn API publication.")
        print(f"Image Path: {img_path}")
        return

    # 4. Publish to LinkedIn
    share_urn = publish(post, str(img_path) if img_path else "")
    print(f"\n[SUCCESS] Published to LinkedIn! URN: {share_urn}")
    if "urn:li:" in share_urn:
        print(f"Live URL: https://www.linkedin.com/feed/update/{share_urn}/")

    # 5. Archive & Log
    archive_md = ARCHIVE_DIR / f"{timestamp}.md"
    archive_md.write_text(
        f"---\ntimestamp: {timestamp}\ntopic: {topic_data.get('topic')}\n"
        f"assignment: {topic_data.get('assignment_num')}\n"
        f"source: {topic_data.get('source')}\nthesis: {thesis}\n"
        f"image: {img_path}\nurn: {share_urn}\n---\n\n{post}\n"
    )
    log_learning(topic_data, post, thesis, str(img_path) if img_path else "", share_urn)
    print(f"[5] Archived to {archive_md} and logged to {LEARNINGS_FILE.name}.")


if __name__ == "__main__":
    main()
