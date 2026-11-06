#!/usr/bin/env python3
"""
retro_tagger.py — Updates local archived post records in ~/posts/daily/ and ~/posts/x/
to inject verified smart tags (@mentions) for portfolio and audit integrity.
"""

import re
from pathlib import Path

POSTS_TO_UPDATE = [
    {
        "file": Path.home() / "posts" / "daily" / "20261106_1001.md",
        "tags": "cc: @Galgotias University @Cyber Secured India @SafeSkillz @Microsoft"
    },
    {
        "file": Path.home() / "posts" / "daily" / "20261105_1948.md",
        "tags": "cc: @Galgotias University @The Linux Foundation @Raspberry Pi"
    },
    {
        "file": Path.home() / "posts" / "x" / "20261106_1549_Linux Privilege Escalation.md",
        "tags": "@GalgotiasGU @cybersecuredin @safeskillz @realtryhackme"
    },
    {
        "file": Path.home() / "posts" / "x" / "20261106_1527_OSINT and Dark Web Recon.md",
        "tags": "@GalgotiasGU @cybersecuredin @safeskillz @realtryhackme @hackthebox_"
    }
]

def retro_tag():
    print("=== RETROACTIVELY TAGGING LOCAL ARCHIVED POSTS ===")
    for item in POSTS_TO_UPDATE:
        p = item["file"]
        if p.exists():
            content = p.read_text(encoding="utf-8", errors="replace")
            tags = item["tags"]
            if tags in content:
                print(f"Already tagged: {p.name}")
                continue

            # Inject tags before hashtags or at the end
            if "#" in content:
                parts = content.rsplit("#", 1)
                new_content = parts[0].rstrip() + "\n\n" + tags + "\n\n#" + parts[1]
            else:
                new_content = content.rstrip() + "\n\n" + tags + "\n"

            p.write_text(new_content, encoding="utf-8")
            print(f"✅ Successfully updated tags in: {p.name}")
        else:
            print(f"File not found: {p}")

if __name__ == "__main__":
    retro_tag()

