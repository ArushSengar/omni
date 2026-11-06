#!/usr/bin/env python3
"""
smart_tagger.py — Context-Aware Smart Tagging & Company Mentions Engine for Arush Sengar.
Automatically detects organizations, internship companies, universities, labs, and tool vendors
from post topics and context, and formats organic @mentions for LinkedIn and X (Twitter)
to maximize impressions, recruiter reach, and corporate reshares.
"""

import re
from typing import Dict, List, Tuple

# Comprehensive Organization & Vendor Registry with exact handles
ENTITY_REGISTRY = {
    "cyber_secured_india": {
        "keywords": ["cyber secured india", "csi", "internship", "assignment"],
        "linkedin": "@Cyber Secured India",
        "twitter": "@cybersecuredin",
        "category": "internship"
    },
    "safeskillz": {
        "keywords": ["safeskillz", "safe skillz", "internship", "assignment"],
        "linkedin": "@SafeSkillz",
        "twitter": "@safeskillz",
        "category": "internship"
    },
    "travelers": {
        "keywords": ["travelers", "travelers india", "travelers insurance"],
        "linkedin": "@Travelers",
        "twitter": "@Travelers",
        "category": "corporate"
    },
    "galgotias_university": {
        "keywords": ["galgotias", "galgotias university", "gu", "college", "student", "bca"],
        "linkedin": "@Galgotias University",
        "twitter": "@GalgotiasGU",
        "category": "university"
    },
    "tryhackme": {
        "keywords": ["tryhackme", "thm", "room", "privesc", "suid", "bandit"],
        "linkedin": "@TryHackMe",
        "twitter": "@realtryhackme",
        "category": "lab_platform"
    },
    "hackthebox": {
        "keywords": ["hackthebox", "hack the box", "htb"],
        "linkedin": "@Hack The Box",
        "twitter": "@hackthebox_",
        "category": "lab_platform"
    },
    "offsec": {
        "keywords": ["offsec", "offensive security", "oscp"],
        "linkedin": "@OffSec",
        "twitter": "@offsectraining",
        "category": "lab_platform"
    },
    "owasp": {
        "keywords": ["owasp", "owasp mas", "owasp top 10", "injection"],
        "linkedin": "@OWASP® Foundation",
        "twitter": "@owasp",
        "category": "community"
    },
    "linux_foundation": {
        "keywords": ["linux", "kernel", "ebpf", "zram", "cgroups"],
        "linkedin": "@The Linux Foundation",
        "twitter": "@linuxfoundation",
        "category": "open_source"
    },
    "python_foundation": {
        "keywords": ["python", "tracemalloc", "asyncio", "gil"],
        "linkedin": "@Python Software Foundation",
        "twitter": "@ThePSF",
        "category": "open_source"
    },
    "docker": {
        "keywords": ["docker", "container", "microservice", "dockerfile"],
        "linkedin": "@Docker, Inc",
        "twitter": "@Docker",
        "category": "vendor"
    },
    "cloudflare": {
        "keywords": ["cloudflare", "dns", "cdn", "ddos"],
        "linkedin": "@Cloudflare",
        "twitter": "@Cloudflare",
        "category": "vendor"
    },
    "vercel": {
        "keywords": ["vercel", "serverless", "nextjs", "edge"],
        "linkedin": "@Vercel",
        "twitter": "@vercel",
        "category": "vendor"
    },
    "github": {
        "keywords": ["github", "git", "ci/cd", "actions", "repo"],
        "linkedin": "@GitHub",
        "twitter": "@github",
        "category": "vendor"
    }
}


def detect_relevant_entities(topic_data: dict) -> List[str]:
    """Scans topic metadata, title, labs, and context for relevant entities."""
    text_corpus = " ".join([
        str(topic_data.get("topic", "")),
        str(topic_data.get("category", "")),
        str(topic_data.get("context", "")),
        str(topic_data.get("platform", "")),
        str(topic_data.get("source", "")),
        " ".join(topic_data.get("labs", [])),
        " ".join(topic_data.get("tags", []))
    ]).lower()

    detected = []
    source = topic_data.get("source", "")
    is_assignment = bool(topic_data.get("assignment_num")) or source == "assignment"

    # Rule 1: Always include university for student context
    detected.append("galgotias_university")

    # Rule 2: If assignment, always include internship companies
    if is_assignment:
        detected.append("cyber_secured_india")
        detected.append("safeskillz")

    # Rule 3: Match keyword patterns
    for entity_id, meta in ENTITY_REGISTRY.items():
        if entity_id in detected:
            continue
        for kw in meta["keywords"]:
            if re.search(r'\b' + re.escape(kw) + r'\b', text_corpus):
                detected.append(entity_id)
                break

    return detected


def generate_smart_tags(topic_data: dict, platform: str = "linkedin") -> Tuple[List[str], str]:
    """
    Returns:
      (list of entity IDs, formatted string ready for injection into post footer or body)
    """
    entities = detect_relevant_entities(topic_data)
    platform = platform.lower()

    if platform in ["linkedin", "li"]:
        tags = [ENTITY_REGISTRY[e]["linkedin"] for e in entities if e in ENTITY_REGISTRY]
        # Keep 3 to 5 tags for natural engagement without spamming
        selected_tags = tags[:5]
        formatted = "cc: " + " ".join(selected_tags)
        return entities, formatted

    elif platform in ["twitter", "x"]:
        tags = [ENTITY_REGISTRY[e]["twitter"] for e in entities if e in ENTITY_REGISTRY]
        # X has strict character limit, pick top 2-3 most relevant handles
        selected_tags = tags[:3]
        formatted = " ".join(selected_tags)
        return entities, formatted

    return entities, ""


def inject_tags_into_linkedin(post_content: str, topic_data: dict) -> str:
    """Seamlessly appends or integrates company mentions into LinkedIn post."""
    _, tag_footer = generate_smart_tags(topic_data, platform="linkedin")
    if not tag_footer:
        return post_content

    # Check if tags are already present
    if "cc: @" in post_content or "Cyber Secured India" in post_content and "@Cyber Secured India" in post_content:
        return post_content

    # Clean placement right above hashtags
    lines = post_content.strip().splitlines()
    hashtag_idx = -1
    for i in range(len(lines) - 1, -1, -1):
        if "#" in lines[i]:
            hashtag_idx = i
            break

    if hashtag_idx != -1:
        lines.insert(hashtag_idx, "")
        lines.insert(hashtag_idx + 1, tag_footer)
        lines.insert(hashtag_idx + 2, "")
        return "\n".join(lines).strip()
    else:
        return post_content.strip() + "\n\n" + tag_footer


def inject_tags_into_tweet(tweet_content: str, topic_data: dict) -> str:
    """Appends targeted handle(s) to tweet if space permits (< 280 chars)."""
    _, tag_footer = generate_smart_tags(topic_data, platform="twitter")
    if not tag_footer:
        return tweet_content

    combined = f"{tweet_content.strip()} {tag_footer}"
    if len(combined) <= 278:
        return combined

    # Try top 1 tag only
    top_tag = tag_footer.split()[0] if tag_footer else ""
    if top_tag and len(f"{tweet_content.strip()} {top_tag}") <= 278:
        return f"{tweet_content.strip()} {top_tag}"

    return tweet_content


if __name__ == "__main__":
    test_assignment = {
        "topic": "Linux Privilege Escalation via SUID Binaries",
        "assignment_num": "7",
        "source": "assignment",
        "context": "TryHackMe lab room privesc, escalated using find SUID binary.",
        "labs": ["TryHackMe"]
    }
    ents, li_str = generate_smart_tags(test_assignment, "linkedin")
    print("Detected Entities:", ents)
    print("LinkedIn Tag Line:", li_str)

    sample_post = "Completed my lab on Linux privilege escalation.\n\n#CyberSecurity #Linux"
    tagged_post = inject_tags_into_linkedin(sample_post, test_assignment)
    print("\n--- Tagged Post ---")
    print(tagged_post)

