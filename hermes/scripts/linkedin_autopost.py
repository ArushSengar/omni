#!/usr/bin/env python3
"""linkedin_autopost.py — post a draft + image to LinkedIn using the saved
persistent session (profile: ~/.linkedin-profile). One-time human login
already done; this script only publishes. Usage:
  python3 linkedin_autopost.py "<post text>" [image_path]
"""
import os
import sys

# Self-dispatch to hermes virtualenv where playwright is installed
VENV_PYTHON = "/home/arush/.hermes/installs/c4e5f05fc62c46c7/environments/c3eca3e27a664bb2929bbedfcbc483b7/venv/bin/python3"
if sys.executable != VENV_PYTHON and os.path.exists(VENV_PYTHON):
    os.execv(VENV_PYTHON, [VENV_PYTHON] + sys.argv)

import re
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

POST_TEXT = sys.argv[1] if len(sys.argv) > 1 else ""
IMAGE = sys.argv[2] if len(sys.argv) > 2 else ""
PROFILE = "/home/arush/.linkedin-profile"
SHOT_DIR = Path("/home/arush/.linkedin-profile/shots")
SHOT_DIR.mkdir(exist_ok=True)

assert POST_TEXT.strip(), "Post text required"

# If text contains LinkedIn API mention format @[Name](urn:li:organization:123), convert to @Name for browser typing
POST_TEXT = re.sub(r'@\[([^\]]+)\]\(urn:li:[^\)]+\)', r'@\1', POST_TEXT)


def shot(page, name):
    page.screenshot(path=str(SHOT_DIR / f"{name}.png"))
    print(f"[shot] {name}.png")


with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        PROFILE,
        headless=True,
        args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
    )
    page = ctx.pages[0] if ctx.pages else ctx.new_page()

    page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(5000)

    # Session check: if redirected to login, abort.
    if "/uas/login" in page.url or "authwall" in page.url:
        print("ERROR: session expired — not logged in. Re-login needed.")
        ctx.close()
        sys.exit(1)
    print(f"[ok] logged in, at {page.url}")
    shot(page, "01_feed")

    # Open the composer
    page.goto("https://www.linkedin.com/post/new/", wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(5000)
    print("[ok] composer page loaded:", page.url)
    shot(page, "02_sharebox")

    # Fill editor
    editor = None
    for sel in [
        'div[role="textbox"][contenteditable="true"]',
        'div[contenteditable="true"][aria-label*="post"]',
        'div[contenteditable="true"]',
        'p[data-placeholder*="What do you want"]',
        'div[role="textbox"]',
    ]:
        try:
            el = page.locator(sel).first
            if el.is_visible(timeout=3000):
                editor = el
                break
        except Exception:
            continue
    if not editor:
        print("ERROR: editor not found")
        shot(page, "02b_nofind")
        ctx.close()
        sys.exit(1)
    editor.click()
    page.keyboard.type(POST_TEXT, delay=15)
    page.wait_for_timeout(1500)
    print("[ok] text typed")
    shot(page, "03_text")

    # Attach image
    if IMAGE:
        attached = False
        for sel in ['input[type="file"]', 'input[accept*="image"]', 'input[type=file][multiple]']:
            try:
                f = page.locator(sel).first
                if f.count() > 0:
                    f.set_input_files(IMAGE, timeout=10000)
                    attached = True
                    break
            except Exception:
                continue
        if not attached:
            print("WARN: no file input found — maybe image button needed")
        page.wait_for_timeout(6000)
        print("[ok] image attached" if attached else "[warn] image attach skipped")
        shot(page, "04_image")

    # Click Post
    posted = False
    for sel in [
        'button[aria-label*="Post"][aria-label*="now"]',
        'button.share-actions__primary-action',
        'button:has-text("Post")',
        'div.share-actions__primary-action button',
    ]:
        try:
            btn = page.locator(sel).first
            if btn.is_visible(timeout=3000):
                btn.click(timeout=8000)
                posted = True
                break
        except Exception:
            continue
    if not posted:
        print("ERROR: Post button not found")
        shot(page, "05_nopost")
        ctx.close()
        sys.exit(1)

    # Wait for post to go through (share box closes / toast)
    page.wait_for_timeout(8000)
    shot(page, "06_afterpost")
    print("[ok] Post button clicked — waiting for confirmation")
    ctx.close()
    print("DONE")
