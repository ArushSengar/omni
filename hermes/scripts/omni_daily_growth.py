#!/usr/bin/env python3
"""
omni_daily_growth.py — Master Unified Autonomous Growth Engine for Arush Sengar.
Publishes high-engagement, humanized technical content simultaneously to LinkedIn and X (Twitter).
Powered by Autonomous Daily Research, TryHackMe/OWASP assignment archives, Context-Aware Smart Tagging,
and 1200x1200 dark terminal proofs.

Scheduled Daily at 7:00 AM IST via Raspberry Pi Cron.

Usage:
  python3 ~/omni_daily_growth.py                   # Full auto daily run (LinkedIn + X)
  python3 ~/omni_daily_growth.py --dry-run         # Compose & render without publishing
  python3 ~/omni_daily_growth.py --research        # Force fresh autonomous research topic
  python3 ~/omni_daily_growth.py --assignment 7    # Force specific assignment
  python3 ~/omni_daily_growth.py --topic "X"       # Force custom topic
"""

import os
import sys
sys.path.insert(0, "/home/arush")

import argparse
import json
import sqlite3
import time
from datetime import datetime
from pathlib import Path

# Core modules
import linkedin_activity_detector
import linkedin_copywriter
import linkedin_collage_generator
import linkedin_daily_post
import x_copywriter
import x_daily_post
import autonomous_researcher
import smart_tagger

try:
    import omni_deduplicator
except ImportError:
    from hermes.scripts import omni_deduplicator

GROWTH_LOG = Path.home() / ".hermes" / "growth_engine_history.json"
GROWTH_LOG.parent.mkdir(parents=True, exist_ok=True)


def record_to_django_db(topic_data, li_post, x_tweets, img_path, published_results):
    """Syncs published post record into Django SQLite database."""
    db_paths = [
        Path.home() / "omni_hub" / "db.sqlite3",
        Path(__file__).resolve().parent.parent.parent / "omni_hub" / "db.sqlite3"
    ]
    for p in db_paths:
        if p.exists():
            try:
                conn = sqlite3.connect(p)
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO growth_growthpost 
                    (title, domain, source, linkedin_content, twitter_content, image_path, status, linkedin_urn, twitter_url, likes, views, comments, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, 0, ?)
                """, (
                    topic_data.get("topic", "Daily Technical Growth"),
                    topic_data.get("category", "Systems Engineering"),
                    topic_data.get("source", "autonomous"),
                    li_post,
                    x_tweets[0] if x_tweets else "",
                    img_path,
                    "PUBLISHED",
                    published_results.get("linkedin", ""),
                    str(published_results.get("x", "")),
                    datetime.now().isoformat()
                ))
                conn.commit()
                conn.close()
                print(f"    [Django Hub] Synced published record to {p}")
                break
            except Exception as e:
                print(f"    [warn] Failed to sync to Django DB: {e}")


def run_growth_pipeline(force_assignment=None, force_topic=None, force_research=False, dry_run=False, platform="all"):
    print("=" * 65)
    print("      🚀 OMNI UNIFIED AUTONOMOUS GROWTH ENGINE (7:00 AM IST)     ")
    print("=" * 65)

    # 1. Topic Selection / Autonomous Research
    dedup = omni_deduplicator.OmniDeduplicator()
    print("\n[1] Detecting Today's Topic & Technical Backlog...")
    if force_research:
        print("    [Autonomous Researcher] Generating cutting-edge research topic...")
        topic_data = autonomous_researcher.research_fresh_topic(dedup=dedup)
    elif force_assignment:
        topic_data = linkedin_activity_detector.detect_daily_topic(force_assignment=force_assignment)
    elif force_topic:
        topic_data = linkedin_activity_detector.detect_daily_topic(force_topic=force_topic)
    else:
        topic_data = linkedin_activity_detector.detect_daily_topic()

    # Pre-publish deduplication validation
    if not (force_assignment or force_topic):
        valid, reason, _ = dedup.evaluate_candidate(topic_data)
        if not valid:
            print(f"    [Deduplicator Override] Topic '{topic_data.get('topic')}' rejected: {reason}")
            print("    [Growth Engine] Autonomously switching to novel research topic...")
            topic_data = autonomous_researcher.research_fresh_topic(dedup=dedup)

    print(f"    Topic Selected : {topic_data.get('topic')}")
    print(f"    Category       : {topic_data.get('category', 'Engineering')}")
    print(f"    Source         : {topic_data.get('source')}")
    print(f"    Assignment #   : {topic_data.get('assignment_num') or 'N/A'}")
    print(f"    Platform/Lab   : {topic_data.get('platform')}")

    # 2. Compose LinkedIn Long-Form Post with Smart Tagging & Anti-AI Validation
    print("\n[2.1] Composing LinkedIn Long-Form Post (Human Student Builder Voice)...")
    li_post = None
    for attempt in range(3):
        angle = "" if attempt == 0 else "STRICT: Do not include preambles, dividers (---), or markdown asterisks."
        post_candidate, li_thesis, _ = linkedin_copywriter.generate_post(topic_data, angle_modifier=angle)
        ok, reason = linkedin_copywriter.validate_post(post_candidate)
        if ok:
            li_post = post_candidate
            break
        print(f"    [warn] LinkedIn attempt {attempt + 1} rejected ({reason}), retrying...")
    if not li_post:
        li_post = linkedin_copywriter.sanitize_human_post(post_candidate)
    words = len(li_post.split())
    print(f"    LinkedIn Post Generated ({words} words)")

    # 3. Compose X/Twitter Post with Smart Mentions & Validation
    print("\n[2.2] Composing X (Twitter) Post with Smart Mentions...")
    x_tweets = None
    for attempt in range(3):
        angle = "" if attempt == 0 else "STRICT: Under 250 characters, zero filler, no quotes or preambles."
        x_result = x_copywriter.generate_tweet(topic_data, format_type="single", angle_modifier=angle)
        candidate_tweets = x_result["tweets"]
        ok, reason = x_copywriter.validate_tweets(candidate_tweets)
        if ok:
            x_tweets = candidate_tweets
            break
        print(f"    [warn] X attempt {attempt + 1} rejected ({reason}), retrying...")
    if not x_tweets:
        x_tweets = [x_copywriter.sanitize_tweet_text(candidate_tweets[0])]
    print(f"    X Tweet Generated ({len(x_tweets[0])} chars): {x_tweets[0][:80]}...")

    # 4. Generate Visual Proof
    print("\n[3] Rendering 1200x1200 Authentic Visual Proof...")
    dt_str = datetime.now().strftime("%Y%m%d_%H%M")
    out_img = Path.home() / "posts" / "daily" / f"{dt_str}_proof.png"
    out_img.parent.mkdir(parents=True, exist_ok=True)

    try:
        linkedin_collage_generator.render_collage(topic_data, str(out_img))
        img_path = str(out_img)
        print(f"    Visual Created: {img_path} ({os.path.getsize(img_path)} bytes)")
    except Exception as e:
        print(f"    [warn] Visual generation failed ({e}), proceeding text-only.")
        img_path = ""

    # Preview / Dry-run
    if dry_run:
        print("\n" + "=" * 65)
        print("[DRY-RUN / PREVIEW MODE] Content Generated Successfully!")
        print("=" * 65)
        print("\n--- LINKEDIN PREVIEW ---")
        print(li_post)
        print("\n--- X (TWITTER) PREVIEW ---")
        for tw in x_tweets:
            print(tw)
        print(f"\nImage Path: {img_path}")
        print("=" * 65)
        return

    # 5. Execute Publishing
    published_results = {}

    # LinkedIn Publishing
    if platform in ["all", "linkedin"]:
        print("\n[4.1] Publishing to LinkedIn...")
        try:
            li_urn = linkedin_daily_post.publish(li_post, img_path)
            print(f"    ✅ LinkedIn Published! URN: {li_urn}")
            published_results["linkedin"] = li_urn
        except Exception as e:
            print(f"    ❌ LinkedIn Failed: {e}")
            published_results["linkedin"] = f"failed: {e}"

    # X / Twitter Publishing
    if platform in ["all", "x", "twitter"]:
        print("\n[4.2] Publishing to X (Twitter) via Free Headless Engine...")
        try:
            x_ids = x_daily_post.publish(x_tweets, img_path)
            print(f"    ✅ X (Twitter) Published! Status: {x_ids}")
            published_results["x"] = x_ids
        except Exception as e:
            print(f"    ❌ X (Twitter) Failed: {e}")
            published_results["x"] = f"failed: {e}"

    # 6. Archive & Sync State to JSON Ledgers & Django DB Atomically
    print("\n[5] Synchronizing Published Post across Unified Ledgers...")
    try:
        omni_deduplicator.commit_published_record(topic_data, li_post, x_tweets, img_path, published_results)
    except Exception as e:
        print(f"    [warn] Unified commit failed ({e}), falling back to standard history log.")
        log_record = {
            "timestamp": datetime.now().isoformat(),
            "topic": topic_data.get("topic"),
            "category": topic_data.get("category"),
            "source": topic_data.get("source"),
            "linkedin_post": li_post,
            "x_tweets": x_tweets,
            "image_path": img_path,
            "results": published_results
        }
        history = []
        if GROWTH_LOG.exists():
            try:
                history = json.loads(GROWTH_LOG.read_text())
            except Exception:
                history = []
        history.append(log_record)
        GROWTH_LOG.write_text(json.dumps(history, indent=2))
        record_to_django_db(topic_data, li_post, x_tweets, img_path, published_results)

    print("\n" + "=" * 65)
    print("🎉 OMNI DAILY GROWTH PIPELINE COMPLETED SUCCESSFULLY!")
    print("=" * 65)


def main():
    parser = argparse.ArgumentParser(description="Master Unified Autonomous Growth Engine for Arush Sengar")
    parser.add_argument("--dry-run", action="store_true", help="Preview without publishing")
    parser.add_argument("--research", action="store_true", help="Force fresh autonomous technical research topic")
    parser.add_argument("--assignment", type=int, help="Force specific assignment number")
    parser.add_argument("--topic", type=str, help="Force custom topic string")
    parser.add_argument("--platform", choices=["all", "linkedin", "x"], default="all", help="Target platform")
    args = parser.parse_args()

    run_growth_pipeline(
        force_assignment=args.assignment,
        force_topic=args.topic,
        force_research=args.research,
        dry_run=args.dry_run,
        platform=args.platform
    )


if __name__ == "__main__":
    main()
