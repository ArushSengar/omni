#!/usr/bin/env python3
"""
smart_tagger.py — Context-Aware Smart Tagging & Company Mentions Engine for Arush Sengar.
Automatically detects organizations, internship companies, universities, labs, and tool vendors
from post topics and context, and formats organic @mentions for LinkedIn and X (Twitter)
to maximize impressions, recruiter reach, and corporate reshares.

CRITICAL LINKEDIN MENTION RULE:
LinkedIn REST API requires the entity mention format:
  @[DisplayName](urn:li:organization:<ORG_ID>)
Raw plain text "@Name" is rendered as inert text and NEVER converts to a clickable pill.
All organization IDs below are verified directly via LinkedIn API v2.
"""

import re
from typing import Dict, List, Tuple

# Comprehensive Organization & Vendor Registry with verified LinkedIn Organization URNs & handles
ENTITY_REGISTRY = {
    "cyber_secured_india": {
        "keywords": ["cyber secured india", "csi", "internship", "assignment"],
        "display_name": "Cyber Secured India",
        "alt_names": ["CyberSecuredIndia"],
        "org_id": "82269037",
        "urn": "urn:li:organization:82269037",
        "linkedin_mention": "@[Cyber Secured India](urn:li:organization:82269037)",
        "twitter": "@cybersecuredin",
        "category": "internship"
    },
    "safeskillz": {
        "keywords": ["safeskillz", "safe skillz", "internship", "assignment"],
        "display_name": "Safe Skillz",
        "alt_names": ["SafeSkillz"],
        "org_id": "105485317",
        "urn": "urn:li:organization:105485317",
        "linkedin_mention": "@[Safe Skillz](urn:li:organization:105485317)",
        "twitter": "@safeskillz",
        "category": "internship"
    },
    "galgotias_university": {
        "keywords": ["galgotias", "galgotias university", "gu", "college", "student", "bca"],
        "display_name": "Galgotias University",
        "alt_names": ["GalgotiasUniversity", "Galgotias"],
        "org_id": "14452491",
        "urn": "urn:li:organization:14452491",
        "linkedin_mention": "@[Galgotias University](urn:li:organization:14452491)",
        "twitter": "@GalgotiasGU",
        "category": "university"
    },
    "tryhackme": {
        "keywords": ["tryhackme", "thm", "room", "privesc", "suid", "bandit"],
        "display_name": "TryHackMe",
        "alt_names": ["Try Hack Me"],
        "org_id": "14055650",
        "urn": "urn:li:organization:14055650",
        "linkedin_mention": "@[TryHackMe](urn:li:organization:14055650)",
        "twitter": "@realtryhackme",
        "category": "lab_platform"
    },
    "hackthebox": {
        "keywords": ["hackthebox", "hack the box", "htb"],
        "display_name": "Hack The Box",
        "alt_names": ["HackTheBox"],
        "org_id": "13305381",
        "urn": "urn:li:organization:13305381",
        "linkedin_mention": "@[Hack The Box](urn:li:organization:13305381)",
        "twitter": "@hackthebox_",
        "category": "lab_platform"
    },
    "offsec": {
        "keywords": ["offsec", "offensive security", "oscp"],
        "display_name": "OffSec",
        "alt_names": ["Offensive Security"],
        "org_id": "5384047",
        "urn": "urn:li:organization:5384047",
        "linkedin_mention": "@[OffSec](urn:li:organization:5384047)",
        "twitter": "@offsectraining",
        "category": "lab_platform"
    },
    "owasp": {
        "keywords": ["owasp", "owasp mas", "owasp top 10", "injection"],
        "display_name": "OWASP® Foundation",
        "alt_names": ["OWASP Foundation", "OWASP"],
        "org_id": "250673",
        "urn": "urn:li:organization:250673",
        "linkedin_mention": "@[OWASP® Foundation](urn:li:organization:250673)",
        "twitter": "@owasp",
        "category": "community"
    },
    "linux_foundation": {
        "keywords": ["linux", "kernel", "ebpf", "zram", "cgroups"],
        "display_name": "The Linux Foundation",
        "alt_names": ["Linux Foundation"],
        "org_id": "208777",
        "urn": "urn:li:organization:208777",
        "linkedin_mention": "@[The Linux Foundation](urn:li:organization:208777)",
        "twitter": "@linuxfoundation",
        "category": "open_source"
    },
    "docker": {
        "keywords": ["docker", "container", "microservice", "dockerfile"],
        "display_name": "Docker, Inc",
        "alt_names": ["Docker"],
        "org_id": "1301808",
        "urn": "urn:li:organization:1301808",
        "linkedin_mention": "@[Docker, Inc](urn:li:organization:1301808)",
        "twitter": "@Docker",
        "category": "vendor"
    },
    "cloudflare": {
        "keywords": ["cloudflare", "dns", "cdn", "ddos"],
        "display_name": "Cloudflare",
        "alt_names": [],
        "org_id": "407222",
        "urn": "urn:li:organization:407222",
        "linkedin_mention": "@[Cloudflare](urn:li:organization:407222)",
        "twitter": "@Cloudflare",
        "category": "vendor"
    },
    "vercel": {
        "keywords": ["vercel", "serverless", "nextjs", "edge"],
        "display_name": "Vercel",
        "alt_names": [],
        "org_id": "16181286",
        "urn": "urn:li:organization:16181286",
        "linkedin_mention": "@[Vercel](urn:li:organization:16181286)",
        "twitter": "@vercel",
        "category": "vendor"
    },
    "github": {
        "keywords": ["github", "git", "ci/cd", "actions", "repo"],
        "display_name": "GitHub",
        "alt_names": [],
        "org_id": "1418841",
        "urn": "urn:li:organization:1418841",
        "linkedin_mention": "@[GitHub](urn:li:organization:1418841)",
        "twitter": "@github",
        "category": "vendor"
    },
    "travelers": {
        "keywords": ["travelers", "travelers india", "travelers insurance"],
        "display_name": "Travelers",
        "alt_names": [],
        "org_id": "3088",
        "urn": "urn:li:organization:3088",
        "linkedin_mention": "@[Travelers](urn:li:organization:3088)",
        "twitter": "@Travelers",
        "category": "corporate"
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


def convert_raw_mentions_to_api(text: str) -> str:
    """
    Finds any raw @mentions in text and upgrades them to LinkedIn API format:
    @[DisplayName](urn:li:organization:ID).
    Also handles variations like @SafeSkillz -> @[Safe Skillz](urn:li:organization:105485317).
    """
    for entity_id, meta in ENTITY_REGISTRY.items():
        disp = meta["display_name"]
        urn = meta["urn"]
        mention = meta["linkedin_mention"]
        if f"({urn})" in text:
            continue
        variations = [disp] + meta.get("alt_names", [])
        for var in variations:
            if not var:
                continue
            pattern = re.compile(r'@' + re.escape(var) + r'(?=[^\w]|$)', re.IGNORECASE)
            text = pattern.sub(mention, text)
    return text


def relocate_cc_line(text: str) -> str:
    """
    Ensures any 'cc: @...' or 'cc: @[...]' line is placed neatly right above hashtags,
    never buried awkwardly inside body paragraphs.
    """
    # Extract cc block
    cc_pattern = re.compile(r'(?:^|\n)(cc:\s*(?:@(?:\[[^\]]+\]\(urn:li:[^\)]+\)|[A-Za-z0-9_®\s]+)\s*)+)', re.MULTILINE)
    m = cc_pattern.search(text)
    if not m:
        # Check inline cc:
        inline_m = re.search(r'(cc:\s*(?:@\[[^\]]+\]\(urn:li:[^\)]+\)\s*)+)', text)
        if not inline_m:
            return text
        cc_block = inline_m.group(1).strip()
        text = text[:inline_m.start()] + text[inline_m.end():]
    else:
        cc_block = m.group(1).strip()
        text = text[:m.start()] + text[m.end():]

    # Clean double spaces or lines
    text = re.sub(r'\n{3,}', '\n\n', text).strip()

    # Find hashtags to place cc: right above them
    lines = text.splitlines()
    h_idx = -1
    for i in range(len(lines) - 1, -1, -1):
        if "#" in lines[i]:
            h_idx = i
            break

    if h_idx != -1:
        lines.insert(h_idx, "")
        lines.insert(h_idx + 1, cc_block)
        lines.insert(h_idx + 2, "")
        return "\n".join(lines).strip()
    else:
        return text.strip() + "\n\n" + cc_block


def generate_smart_tags(topic_data: dict, platform: str = "linkedin", mode: str = "api") -> Tuple[List[str], str]:
    """
    Returns:
      (list of entity IDs, formatted string ready for injection into post footer or body)
      mode: 'api' for official LinkedIn mention URNs (e.g. @[Name](urn:li:organization:...)),
            'clean' for human-readable display (e.g. @Name).
    """
    entities = detect_relevant_entities(topic_data)
    platform = platform.lower()

    if platform in ["linkedin", "li"]:
        if mode == "api":
            tags = [ENTITY_REGISTRY[e]["linkedin_mention"] for e in entities if e in ENTITY_REGISTRY]
        else:
            tags = [f"@{ENTITY_REGISTRY[e]['display_name']}" for e in entities if e in ENTITY_REGISTRY]

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


def strip_api_mentions_for_browser(text: str) -> str:
    """Converts @[DisplayName](urn:li:organization:123) into @DisplayName for browser typing."""
    return re.sub(r'@\[([^\]]+)\]\(urn:li:[^\)]+\)', r'@\1', text)


def inject_tags_into_linkedin(post_content: str, topic_data: dict, mode: str = "api") -> str:
    """
    Seamlessly appends or integrates company mentions into LinkedIn post.
    Defaults to mode='api' for authentic LinkedIn API clickable mention pills.
    If post already has raw @mentions (e.g. generated by LLM), they are automatically upgraded to API format
    and relocated neatly right above hashtags.
    """
    if mode == "api":
        post_content = convert_raw_mentions_to_api(post_content)

    if "urn:li:organization:" in post_content:
        return relocate_cc_line(post_content)

    if "cc: @" in post_content:
        if mode == "api":
            post_content = convert_raw_mentions_to_api(post_content)
        return relocate_cc_line(post_content)

    # Otherwise, generate and inject clean tag line
    _, tag_footer = generate_smart_tags(topic_data, platform="linkedin", mode=mode)
    if not tag_footer:
        return post_content

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
    sample_raw = "Great lab. cc: @Galgotias University @Cyber Secured India @SafeSkillz in middle.\n\nTakeaway: Great work.\n\n#CyberSecurity #Linux"
    upgraded = inject_tags_into_linkedin(sample_raw, test_assignment, mode="api")
    print("--- Test Relocate & Upgrade ---")
    print(upgraded)
