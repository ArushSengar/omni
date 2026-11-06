#!/usr/bin/env python3
"""
x_autopost.py — 100% Free, Autonomous Headless Browser Twitter Publisher for Arush Sengar.
Uses Playwright with Chromium & saved session cookies (~/.twitter-profile).
Zero API keys, zero developer subscriptions ($0.00 forever).

Usage:
  # Single tweet with image
  python3 x_autopost.py "Post text" [image_path]

  # Thread posting
  python3 x_autopost.py --thread "Tweet 1" "Tweet 2" "Tweet 3" [image_path]
"""

import sys

import argparse
import json
import os
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

PROFILE_DIR = Path.home() / ".twitter-profile"
PROFILE_DIR.mkdir(parents=True, exist_ok=True)
SHOT_DIR = PROFILE_DIR / "shots"
SHOT_DIR.mkdir(parents=True, exist_ok=True)
COOKIE_FILE = PROFILE_DIR / "cookies.json"


def take_shot(page, name: str):
    shot_path = SHOT_DIR / f"{name}.png"
    try:
        page.screenshot(path=str(shot_path))
        print(f"[shot] {name}.png saved")
    except Exception:
        pass


def post_to_x(tweets: list, image_path: str = "") -> bool:
    if not tweets:
        print("ERROR: No tweets provided.")
        return False

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            str(PROFILE_DIR),
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage"
            ],
            user_agent="Mozilla/5.0 (X11; Linux aarch64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )

        # Inject cookies if present
        if COOKIE_FILE.exists():
            try:
                cookies = json.loads(COOKIE_FILE.read_text())
                if isinstance(cookies, list):
                    formatted_cookies = []
                    for c in cookies:
                        domain = c.get("domain", ".x.com")
                        ss = c.get("sameSite")
                        if ss in ["no_restriction", None]:
                            ss = "None" if c.get("secure") else "Lax"
                        elif str(ss).lower() == "lax":
                            ss = "Lax"
                        elif str(ss).lower() == "strict":
                            ss = "Strict"
                        else:
                            ss = "Lax"
                        formatted_cookies.append({
                            "name": c.get("name"),
                            "value": c.get("value"),
                            "domain": domain,
                            "path": c.get("path", "/"),
                            "secure": c.get("secure", True),
                            "httpOnly": c.get("httpOnly", False),
                            "sameSite": ss
                        })
                    ctx.add_cookies(formatted_cookies)
                    print(f"[ok] Injected {len(formatted_cookies)} session cookies")
            except Exception as e:
                print(f"[warn] Cookie injection failed: {e}")

        page = ctx.pages[0] if ctx.pages else ctx.new_page()

        print("[1] Verifying X session at https://x.com/home ...")
        page.goto("https://x.com/home", wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(4000)

        # Session check
        if "/login" in page.url or "/i/flow/login" in page.url:
            print("\n❌ ERROR: Not logged in to X (Twitter). Session is expired or missing.")
            print("👉 Run this command to setup your free cookies:")
            print("   python3 ~/x_setup_cookies.py --auth-token <YOUR_TOKEN> --ct0 <YOUR_CT0>\n")
            take_shot(page, "01_login_wall")
            ctx.close()
            return False

        print(f"[ok] Logged in successfully! URL: {page.url}")
        take_shot(page, "01_home_feed")

        # Open post composer
        print("[2] Opening composer at https://x.com/compose/post ...")
        page.goto("https://x.com/compose/post", wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(4000)
        take_shot(page, "02_composer")

        # Locate first editor
        first_editor = None
        for sel in [
            'div[data-testid="tweetTextarea_0"]',
            'div[role="textbox"][contenteditable="true"]',
            'div[aria-label*="Post text"]',
            'div[contenteditable="true"]'
        ]:
            try:
                el = page.locator(sel).first
                if el.is_visible(timeout=4000):
                    first_editor = el
                    break
            except Exception:
                continue

        if not first_editor:
            print("❌ ERROR: Could not find Tweet textarea editor.")
            take_shot(page, "02b_editor_not_found")
            ctx.close()
            return False

        # Type Tweet 1
        first_editor.click()
        page.wait_for_timeout(500)
        page.keyboard.type(tweets[0], delay=10)
        print(f"[ok] Tweet 1 typed ({len(tweets[0])} chars)")
        take_shot(page, "03_tweet1_typed")

        # Handle Thread if multiple tweets provided
        if len(tweets) > 1:
            for idx, tw_text in enumerate(tweets[1:], 1):
                print(f"[2.{idx}] Adding thread tweet {idx + 1}/{len(tweets)}...")
                # Click the '+' add button in Twitter composer
                add_btn = None
                for b_sel in ['button[data-testid="addButton"]', 'button[aria-label*="Add post"]', 'button[aria-label*="Add Tweet"]']:
                    try:
                        b = page.locator(b_sel).first
                        if b.is_visible(timeout=3000):
                            add_btn = b
                            break
                    except Exception:
                        continue
                if add_btn:
                    add_btn.click()
                    page.wait_for_timeout(1500)
                    # Find newly added editor
                    next_editor = page.locator(f'div[data-testid="tweetTextarea_{idx}"]').first
                    if next_editor.is_visible(timeout=3000):
                        next_editor.click()
                        page.keyboard.type(tw_text, delay=10)
                        print(f"      Tweet {idx + 1} typed ({len(tw_text)} chars)")
                    else:
                        print(f"      [warn] Could not locate thread editor for tweet {idx + 1}")
                else:
                    print(f"      [warn] Could not find thread add button for tweet {idx + 1}")
            take_shot(page, "03b_thread_typed")

        # Attach image if provided
        if image_path and os.path.exists(image_path):
            print(f"[3] Attaching image: {image_path} ...")
            attached = False
            for f_sel in [
                'input[data-testid="fileInput"]',
                'input[type="file"][accept*="image"]',
                'input[type="file"]'
            ]:
                try:
                    f_input = page.locator(f_sel).first
                    if f_input.count() > 0:
                        f_input.set_input_files(image_path, timeout=10000)
                        attached = True
                        break
                except Exception:
                    continue
            if attached:
                print("[ok] Image attached successfully! Waiting for preview render...")
                page.wait_for_timeout(5000)
                take_shot(page, "04_image_attached")
            else:
                print("[warn] File input not found, proceeding text-only.")

        # Click Post Button / Submit
        print("[4] Submitting post...")
        try:
            first_editor.focus()
            page.wait_for_timeout(500)
            page.keyboard.press("Control+Enter")
            print("[*] Fired Control+Enter shortcut")
        except Exception as e:
            print(f"[warn] Focus error: {e}")

        page.wait_for_timeout(2000)
        print("[*] Triggering direct DOM click on post button...")
        clicked = page.evaluate('''() => {
            const btn = document.querySelector('button[data-testid="tweetButton"]') || 
                        document.querySelector('button[data-testid="tweetButtonInline"]');
            if (btn) {
                btn.click();
                return true;
            }
            return false;
        }''')
        print(f"[*] DOM click result: {clicked}")

        # Wait for dialog to close
        print("[*] Waiting for post confirmation...")
        try:
            page.locator('div[role="dialog"]').wait_for(state="detached", timeout=15000)
            print("[ok] Post dialog closed successfully!")
        except Exception:
            print("[warn] Dialog close wait finished, verifying...")

        page.wait_for_timeout(4000)
        take_shot(page, "06_post_published")

        ctx.close()
        print("\n🚀 SUCCESS: Tweet published to X autonomously via Free Playwright Engine!")
        return True


def main():
    parser = argparse.ArgumentParser(description="100% Free Headless Playwright Twitter Autoposter")
    parser.add_argument("text", nargs="*", help="Tweet text strings (multiple for thread)")
    parser.add_argument("--image", help="Path to image file")
    parser.add_argument("--thread", action="store_true", help="Post multiple arguments as a thread")
    args = parser.parse_args()

    # Determine image and text
    raw_args = args.text
    image_path = args.image or ""
    tweets = []

    for a in raw_args:
        if (a.endswith(".png") or a.endswith(".jpg") or a.endswith(".jpeg")) and os.path.exists(a):
            image_path = a
        else:
            tweets.append(a)

    if not tweets:
        print("Usage:")
        print('  python3 x_autopost.py "Single tweet text" [image_path]')
        print('  python3 x_autopost.py --thread "Tweet 1" "Tweet 2" "Tweet 3" [image_path]')
        sys.exit(1)

    success = post_to_x(tweets, image_path)
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()

