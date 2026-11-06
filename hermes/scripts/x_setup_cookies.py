#!/usr/bin/env python3
"""
x_setup_cookies.py — One-time 100% Free Twitter Login Session Setup for Arush Sengar.
Saves browser cookies to ~/.twitter-profile/cookies.json so Playwright can post to X
autonomously without any paid API keys or developer fees ($0.00 forever).

Usage:
  # Option 1: Quick token pass (from Chrome DevTools -> Application -> Cookies -> https://x.com)
  python3 ~/x_setup_cookies.py --auth-token "YOUR_AUTH_TOKEN" --ct0 "YOUR_CT0"

  # Option 2: From exported cookies JSON file (Cookie-Editor extension)
  python3 ~/x_setup_cookies.py --file /path/to/cookies.json
"""

import argparse
import json
import sys
from pathlib import Path

PROFILE_DIR = Path.home() / ".twitter-profile"
PROFILE_DIR.mkdir(parents=True, exist_ok=True)
COOKIE_FILE = PROFILE_DIR / "cookies.json"

def save_tokens(auth_token: str, ct0: str):
    cookies = [
        {
            "name": "auth_token",
            "value": auth_token.strip(),
            "domain": ".x.com",
            "path": "/",
            "secure": True,
            "httpOnly": True,
            "sameSite": "Lax"
        },
        {
            "name": "ct0",
            "value": ct0.strip(),
            "domain": ".x.com",
            "path": "/",
            "secure": True,
            "httpOnly": False,
            "sameSite": "Lax"
        }
    ]
    COOKIE_FILE.write_text(json.dumps(cookies, indent=2))
    print(f"✅ Cookies successfully saved to: {COOKIE_FILE}")
    print("Playwright is now ready to post to X for free!")

def save_from_file(file_path: str):
    p = Path(file_path)
    if not p.exists():
        sys.exit(f"❌ File not found: {file_path}")
    data = json.loads(p.read_text())
    if isinstance(data, list):
        COOKIE_FILE.write_text(json.dumps(data, indent=2))
        print(f"✅ Imported {len(data)} cookies from {file_path} to {COOKIE_FILE}")
    else:
        sys.exit("❌ Invalid cookie JSON format. Expected list of cookie objects.")

def main():
    parser = argparse.ArgumentParser(description="Setup Twitter cookies for 100% Free Playwright posting")
    parser.add_argument("--auth-token", help="auth_token cookie value from x.com")
    parser.add_argument("--ct0", help="ct0 cookie value from x.com")
    parser.add_argument("--file", help="Path to exported cookies.json file")
    args = parser.parse_args()

    if args.auth_token and args.ct0:
        save_tokens(args.auth_token, args.ct0)
    elif args.file:
        save_from_file(args.file)
    else:
        print("Usage:")
        print("  python3 ~/x_setup_cookies.py --auth-token <TOKEN> --ct0 <CT0>")
        print("  python3 ~/x_setup_cookies.py --file /path/to/cookies.json")
        if COOKIE_FILE.exists():
            print(f"\nCurrent status: Cookies already present at {COOKIE_FILE}")
        else:
            print("\nCurrent status: No cookies configured yet.")

if __name__ == "__main__":
    main()

