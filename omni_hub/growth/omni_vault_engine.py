#!/usr/bin/env python3
"""
omni_vault_engine.py — Core Multimodal Extraction, AI Synthesis & Query Engine for OmniVault.
Author: Arush Sengar (Omni Knowledge & Resource Vault)

Capabilities:
  1. Image / Screenshot OCR & Vision extraction (multi-tool detection from single photo).
  2. Web URL live scraping & metadata extraction.
  3. PDF / Cheatsheet text extraction via PyPDF.
  4. Auto-categorization into 7 primary technical domains.
  5. Punchy 1-line "Kis Kaam Aayega" purpose synthesis.
  6. Legality & Threat Triage (SAFE vs PENTEST_ONLY vs CAUTION vs SUSPICIOUS).
  7. Conversational AI Assistant ("Ask Vault") for natural language tool retrieval.
"""

import os
import sys
import re
import json
import hashlib
import ipaddress
import socket
import threading
import tempfile
import urllib.parse
import urllib.request
import urllib.error
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Tuple

# Dependencies
try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

# OmniRoute Configuration
OMNIROUTE_URLS = [
    os.environ.get("OMNIROUTE_URL", "http://localhost:20128/v1"),
    "http://192.168.0.100:20128/v1",
    "http://127.0.0.1:20128/v1"
]
OMNIROUTE_KEY = os.environ.get("HERMES_CUSTOM_LOCALHOST_20128_API_KEY", "sk-971230e546e14a3e-23822a-06e1aa8d")
MODEL_NAME = os.environ.get("DAILY_MODEL", "auto/best-chat")

# Persistent MD5 In-Memory & Disk Query Cache (0ms latency & 0 API cost for repeat queries)
CACHE_FILE = Path.home() / ".omnivault_llm_cache.json"
_PROMPT_CACHE = {}
_CACHE_LOCK = threading.Lock()

ALLOWED_SCRAPE_PORTS = {None, 80, 443, 8080, 8443}

def _is_ip_restricted(ip_obj: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    """Blocks private, loopback, link-local, reserved, multicast, unspecified, and IPv4-mapped private IPs."""
    if isinstance(ip_obj, ipaddress.IPv6Address) and ip_obj.ipv4_mapped:
        ip_obj = ip_obj.ipv4_mapped
    return (
        ip_obj.is_private or
        ip_obj.is_loopback or
        ip_obj.is_link_local or
        ip_obj.is_reserved or
        ip_obj.is_multicast or
        ip_obj.is_unspecified
    )

def _load_cache():
    global _PROMPT_CACHE
    if CACHE_FILE.exists():
        try:
            _PROMPT_CACHE = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        except Exception:
            _PROMPT_CACHE = {}

def _save_cache():
    global _PROMPT_CACHE
    with _CACHE_LOCK:
        try:
            if len(_PROMPT_CACHE) > 500:
                keys = list(_PROMPT_CACHE.keys())[-400:]
                _PROMPT_CACHE = {k: _PROMPT_CACHE[k] for k in keys}
            trimmed = dict(_PROMPT_CACHE)
            cache_dir = CACHE_FILE.parent
            cache_dir.mkdir(parents=True, exist_ok=True)
            tf = tempfile.NamedTemporaryFile("w", dir=str(cache_dir), delete=False, encoding="utf-8")
            try:
                json.dump(trimmed, tf)
                tf.flush()
                temp_name = tf.name
            finally:
                tf.close()
            os.replace(temp_name, CACHE_FILE)
        except Exception as e:
            print(f"[warn] Failed to atomic write cache: {e}")

_load_cache()

def is_safe_url(url: str) -> bool:
    """Verifies that a URL starts with http:// or https:// and has a valid, non-private hostname."""
    if not url or not isinstance(url, str):
        return False
    try:
        parsed = urllib.parse.urlsplit(url.strip())
        if parsed.scheme.lower() not in ("http", "https") or not parsed.hostname:
            return False
        host = parsed.hostname.lower().strip("[]")
        if host in ("localhost", "0.0.0.0", "127.0.0.1", "::", "::1", "169.254.169.254"):
            return False
        if host.endswith(".local") or host.endswith(".internal"):
            return False
        try:
            ip_obj = ipaddress.ip_address(host)
            if _is_ip_restricted(ip_obj):
                return False
        except ValueError:
            pass
        return True
    except Exception:
        return False

def get_existing_categories_list() -> List[str]:
    """Retrieves list of currently active category names from the database."""
    try:
        from growth.models import VaultResource
        cats = list(VaultResource.objects.values_list('category', flat=True).distinct().order_by('category'))
        return [c.strip() for c in cats if c and c.strip()]
    except Exception:
        return [
            "Claude & Agent Skills",
            "AI & LLM Tools",
            "Cyber Security & Pentesting",
            "Developer & APIs",
            "Linux, Homelab & Systems",
            "Media, Audio & Design",
            "Productivity & Automation",
            "Student & Learning"
        ]


def get_category_icon(category_name: str) -> str:
    """Returns a context-appropriate emoji icon for any dynamic category."""
    c = (category_name or "").lower()
    if "all" in c: return "🌐"
    if "edit" in c or "photo" in c or "crop" in c: return "✂️"
    if "agent" in c or "claude" in c: return "🤖"
    if "ai" in c or "llm" in c or "gpt" in c or "model" in c or "intel" in c: return "🧠"
    if "sec" in c or "hack" in c or "pentest" in c or "osint" in c: return "🛡️"
    if "code" in c or "dev" in c or "api" in c or "sdk" in c: return "💻"
    if "linux" in c or "sys" in c or "home" in c or "server" in c or "bash" in c: return "🐧"
    if "music" in c or "audio" in c or "sound" in c: return "🎵"
    if "video" in c or "film" in c or "stream" in c: return "🎬"
    if "design" in c or "art" in c or "ui" in c: return "🎨"
    if "3d" in c or "cad" in c or "render" in c: return "🧊"
    if "finance" in c or "crypto" in c or "money" in c or "wallet" in c: return "💰"
    if "game" in c or "gaming" in c: return "🎮"
    if "job" in c or "career" in c or "resume" in c: return "💼"
    if "learn" in c or "study" in c or "edu" in c or "student" in c: return "🎓"
    if "scrap" in c or "crawl" in c: return "🕸️"
    if "cloud" in c or "host" in c or "deploy" in c: return "☁️"
    if "productiv" in c or "auto" in c or "task" in c or "flow" in c: return "⚡"
    if "health" in c or "fit" in c or "med" in c: return "❤️"
    return "📁"


def get_category_fa_icon(category_name: str) -> str:
    """Returns a FontAwesome icon class for any dynamic category."""
    c = (category_name or "").lower()
    if "all" in c: return "fa-layer-group"
    if "edit" in c or "photo" in c or "crop" in c: return "fa-crop-simple"
    if "agent" in c or "claude" in c: return "fa-robot"
    if "ai" in c or "llm" in c or "gpt" in c: return "fa-brain"
    if "sec" in c or "pentest" in c or "osint" in c: return "fa-shield-halved"
    if "code" in c or "dev" in c or "api" in c: return "fa-code"
    if "linux" in c or "server" in c or "sys" in c or "bash" in c: return "fa-server"
    if "audio" in c or "music" in c: return "fa-music"
    if "video" in c or "film" in c: return "fa-video"
    if "design" in c or "art" in c: return "fa-palette"
    if "3d" in c: return "fa-cube"
    if "finance" in c or "crypto" in c: return "fa-coins"
    if "game" in c: return "fa-gamepad"
    if "career" in c or "job" in c: return "fa-briefcase"
    if "edu" in c or "learn" in c or "student" in c: return "fa-graduation-cap"
    if "scrap" in c: return "fa-spider"
    if "cloud" in c: return "fa-cloud"
    if "auto" in c or "productiv" in c: return "fa-bolt"
    return "fa-folder"


class _DynamicCategoryIconDict(dict):
    def __getitem__(self, key):
        return get_category_icon(key)
    def get(self, key, default=None):
        return get_category_icon(key)


class _DynamicCategoryFaIconDict(dict):
    def __getitem__(self, key):
        return get_category_fa_icon(key)
    def get(self, key, default=None):
        return get_category_fa_icon(key)


CATEGORY_ICONS = _DynamicCategoryIconDict()
CATEGORY_FA_ICONS = _DynamicCategoryFaIconDict()


TECH_ACRONYMS = {"ai", "llm", "api", "apis", "osint", "pdf", "cad", "sdk", "cli", "ui", "ux", "3d", "sql", "iot", "ctf", "rag"}

def normalize_category_and_subcategory(raw_cat: str, raw_subcat: str = "", existing_categories: List[str] = None) -> Tuple[str, str]:
    """
    Cleans, title-cases, and aligns dynamic categories and subcategories.
    Reuses existing category names (case-insensitively) to prevent duplicates,
    while allowing arbitrary new categories to be born smoothly.
    Preserves uppercase tech acronyms (e.g. AI, LLM, API, OSINT, 3D).
    """
    cat = (raw_cat or "").strip()
    subcat = (raw_subcat or "").strip()

    if not cat:
        if subcat:
            cat = subcat
            subcat = "General"
        else:
            cat = "General Utilities"
            subcat = "Tools"

    def _normalize_phrase(text: str) -> str:
        clean = re.sub(r'[{}\[\]<>;"\'`\n\r\t]', '', text).replace("_", " ").replace("-", " ")
        words = clean.split()
        normalized_words = []
        for w in words:
            lw = w.lower()
            if lw in TECH_ACRONYMS:
                normalized_words.append(lw.upper())
            elif lw in ("and", "&", "of", "the", "in", "for", "to"):
                normalized_words.append(lw)
            else:
                normalized_words.append(w.capitalize())
        result = " ".join(normalized_words).strip()
        if result and result[0].islower():
            result = result[0].upper() + result[1:]
        return result

    cat_normalized = _normalize_phrase(cat)

    # Check case-insensitive match in existing categories
    if existing_categories:
        for ex in existing_categories:
            if ex and ex.strip().lower() == cat_normalized.lower():
                cat_normalized = ex.strip()
                break

    if subcat:
        subcat_normalized = _normalize_phrase(subcat)
    else:
        subcat_normalized = "General"

    if cat_normalized.lower() == subcat_normalized.lower():
        subcat_normalized = "General"

    return cat_normalized, subcat_normalized


def detect_smart_category(title: str = "", category_hint: str = "", subcategory: str = "", tags = None, text_context: str = "", existing_categories: List[str] = None) -> str:
    """Backward-compatible helper that normalizes and returns category."""
    cat, _ = normalize_category_and_subcategory(category_hint, subcategory, existing_categories or get_existing_categories_list())
    return cat



def call_llm(messages: List[Dict], max_tokens: int = 1500, temperature: float = 0.25) -> str:
    """Invokes OmniRoute LLM with fallback support and MD5 prompt caching."""
    cache_key = hashlib.md5(json.dumps(messages, sort_keys=True).encode("utf-8")).hexdigest()
    with _CACHE_LOCK:
        if cache_key in _PROMPT_CACHE:
            return _PROMPT_CACHE[cache_key]

    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature
    }
    data_bytes = json.dumps(payload).encode("utf-8")
    last_err = None

    for base_url in OMNIROUTE_URLS:
        try:
            req = urllib.request.Request(
                f"{base_url}/chat/completions",
                data=data_bytes,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {OMNIROUTE_KEY}"
                }
            )
            with urllib.request.urlopen(req, timeout=45) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                result_text = res["choices"][0]["message"]["content"].strip()
                with _CACHE_LOCK:
                    _PROMPT_CACHE[cache_key] = result_text
                _save_cache()
                return result_text
        except Exception as e:
            last_err = e
            continue

    raise RuntimeError(f"OmniRoute LLM failed across endpoints {OMNIROUTE_URLS}: {last_err}")


# =====================================================================
# INGESTION PREREQUISITES: OCR, WEB & PDF
# =====================================================================

def ocr_image(image_path: str) -> str:
    """Extracts raw text from an image or screenshot using Tesseract OCR."""
    if not os.path.exists(image_path):
        return ""
    try:
        res = subprocess.run(
            ["tesseract", image_path, "stdout", "--oem", "1", "-l", "eng"],
            capture_output=True,
            text=True,
            timeout=25
        )
        return res.stdout.strip()
    except Exception as e:
        print(f"[warn] Tesseract OCR error: {e}")
        return ""


class DisallowPrivateRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Prevents HTTP 301/302 redirects from routing to private, loopback, or unspecified IPs."""
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        parsed = urllib.parse.urlsplit(newurl)
        if parsed.scheme.lower() not in ("http", "https"):
            raise urllib.error.HTTPError(newurl, code, "Forbidden redirection scheme", headers, fp)
        hostname = parsed.hostname
        if not hostname or hostname.lower() in ("localhost", "0.0.0.0", "::", "127.0.0.1"):
            raise urllib.error.HTTPError(newurl, code, "Restricted destination host", headers, fp)
        if parsed.port not in ALLOWED_SCRAPE_PORTS:
            raise urllib.error.HTTPError(newurl, code, f"Forbidden destination port: {parsed.port}", headers, fp)
        try:
            for _, _, _, _, sockaddr in socket.getaddrinfo(hostname, None):
                ip_obj = ipaddress.ip_address(sockaddr[0])
                if _is_ip_restricted(ip_obj):
                    raise urllib.error.HTTPError(newurl, code, f"Forbidden redirect to restricted IP {ip_obj}", headers, fp)
        except socket.gaierror:
            raise urllib.error.HTTPError(newurl, code, "Failed to resolve redirect host", headers, fp)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def crawl_url_metadata(url: str) -> Dict:
    """Scrapes page title, meta description, and primary content from a URL with SSRF & redirect defense."""
    meta = {
        "url": url,
        "title": "",
        "description": "",
        "body_snippet": "",
        "status_code": 0
    }
    try:
        parsed = urllib.parse.urlsplit(url)
        if parsed.scheme.lower() not in ("http", "https"):
            meta["error"] = f"Invalid scheme: {parsed.scheme}. Only HTTP/HTTPS allowed."
            meta["description"] = meta["error"]
            return meta

        hostname = parsed.hostname
        if not hostname or hostname.lower() in ("localhost", "0.0.0.0", "::", "127.0.0.1", "::1"):
            meta["error"] = "Invalid URL: restricted destination host."
            meta["description"] = meta["error"]
            return meta

        if parsed.port not in ALLOWED_SCRAPE_PORTS:
            meta["error"] = f"Security block: Port {parsed.port} is not in allowed scrape ports."
            meta["description"] = meta["error"]
            return meta

        # Resolve hostname and block private, loopback, or reserved IP ranges (SSRF defense)
        addr_infos = socket.getaddrinfo(hostname, None)
        for _, _, _, _, sockaddr in addr_infos:
            ip_str = sockaddr[0]
            ip_obj = ipaddress.ip_address(ip_str)
            if _is_ip_restricted(ip_obj):
                meta["error"] = f"Security block: IP {ip_str} is within private/restricted range."
                meta["description"] = meta["error"]
                return meta

        opener = urllib.request.build_opener(DisallowPrivateRedirectHandler())
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }
        req = urllib.request.Request(url, headers=headers)
        with opener.open(req, timeout=12) as response:
            meta["status_code"] = response.getcode()
            content_type = response.headers.get("Content-Type", "").lower()
            if "text/html" not in content_type and "application/xhtml" not in content_type:
                meta["description"] = f"Skipped non-HTML Content-Type: {content_type}"
                return meta
            raw_bytes = response.read(512 * 1024)  # Cap read at 512KB to protect RAM
            html = raw_bytes.decode("utf-8", errors="replace")

        if BeautifulSoup:
            soup = BeautifulSoup(html, "html.parser")
            meta["title"] = soup.title.string.strip() if soup.title and soup.title.string else ""

            # Check meta description
            desc_tag = soup.find("meta", attrs={"name": re.compile(r"description", re.I)}) or \
                       soup.find("meta", attrs={"property": "og:description"})
            if desc_tag and desc_tag.get("content"):
                meta["description"] = desc_tag["content"].strip()

            # Clean body snippet
            for s in soup(["script", "style", "nav", "footer", "header"]):
                s.decompose()
            text = " ".join(soup.stripped_strings)
            meta["body_snippet"] = text[:2500]
        else:
            meta["body_snippet"] = html[:1500]

    except Exception as e:
        meta["description"] = f"Fetch note: {e}"

    return meta


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extracts text content from a PDF document."""
    if not os.path.exists(pdf_path) or not PdfReader:
        return ""
    try:
        reader = PdfReader(pdf_path)
        pages_text = []
        for p in reader.pages[:20]: # Up to 20 pages
            txt = p.extract_text()
            if txt:
                pages_text.append(txt)
        return "\n\n".join(pages_text)
    except Exception as e:
        print(f"[warn] PyPDF extraction error: {e}")
        return ""


# =====================================================================
# AI EXTRACTION & ENRICHMENT
# =====================================================================

def build_extraction_system_prompt(existing_categories: List[str] = None) -> str:
    """
    Builds the system prompt dynamically injecting existing categories from the database.
    Instructs the LLM on the two-tier hierarchy:
      - If a domain already exists in existing_categories, reuse it and create a specific subcategory.
      - If a domain does NOT exist in existing_categories, dynamically create a brand-new high-level category
        in clean Title Case (e.g. 'Editing', '3D Modeling', 'Cryptocurrency') and a specific subcategory under it.
      - For multi-item inputs (e.g. 5 photo editing websites), assign all to the same parent category.
    Sanitizes category names and caps to top 40 to protect against prompt injection and bloat.
    """
    if not existing_categories:
        existing_categories = get_existing_categories_list()

    # Sanitize category strings and limit to top 40 unique categories
    sanitized_cats = []
    seen = set()
    for c in existing_categories:
        clean_c = re.sub(r'[\r\n\t`"\'<>{}\[\]]', '', str(c)).strip()[:60]
        if clean_c and clean_c.lower() not in seen:
            seen.add(clean_c.lower())
            sanitized_cats.append(clean_c)
        if len(sanitized_cats) >= 40:
            break

    cats_formatted = "\n".join([f"    - {c}" for c in sanitized_cats])

    return f"""You are OmniVault Intelligence, an expert digital knowledge extractor and research librarian built for Arush Sengar.

Your job is to analyze raw input (OCR text from screenshots, web scrapes, PDF text, or user notes) and identify EVERY distinct website, utility, digital trick, or software tool mentioned.

TAXONOMY & DYNAMIC TWO-TIER HIERARCHY RULES:
Every item MUST be assigned both a high-level "category" and a specific "subcategory".

CURRENT EXISTING CATEGORIES IN ARUSH'S VAULT:
{cats_formatted}

RULES FOR CATEGORY & SUBCATEGORY SELECTION:
1. REUSE EXISTING CATEGORY IF A REASONABLE MATCH EXISTS:
   - If one of the existing categories above fits the high-level domain of the item, REUSE that exact category name.
   - Then, create or assign an appropriate, specific "subcategory" under it.
   - Example: If the tool is a Claude Code extension or prompt pack, use category "Claude & Agent Skills" and subcategory "Coding Workflows" or "Agent Skills".
   - Example: If the tool is an audio separation tool and "Media, Audio & Design" or "Editing" exists, use that category and subcategory "Audio Separation".

2. DYNAMICALLY CREATE A NEW CATEGORY IF NO EXISTING ONE FITS:
   - If the item belongs to a domain not covered by the existing categories, DO NOT force it into an unrelated bucket.
   - DYNAMICALLY INVENT A BRAND NEW high-level category in clean Title Case (e.g. "Editing", "3D Modeling", "Finance", "Gaming", "Robotics", "Health & Fitness", etc.).
   - Then, branch a specific "subcategory" under it (e.g. category "Editing", subcategory "Photos" or "Video").

3. MULTI-TOOL BATCH COHESION:
   - If an image or note lists multiple tools of a shared domain (e.g. 5 websites for photo editing), group ALL of them under the same high-level category (e.g. "Editing") and assign fitting subcategories (e.g. "Photos").

FOR EACH TOOL / WEBSITE DETECTED, RETURN A STRICT JSON OBJECT WITH:
- "title": Clean canonical name (e.g. "CyberChef", "v0.dev", "Photoroom", "Pixlr").
- "url": Real canonical URL (e.g. "https://photoroom.com"). If not explicit, deduce the official domain.
- "one_liner": A punchy, crystal-clear 1-sentence explanation in simple Hindi/English student-friendly language explaining EXACTLY what this tool does and what it is used for (e.g. "1 click mein photo se background erase karke high quality PNG export karne ke liye"). NEVER use generic corporate fluff.
- "category": High-level domain (reused from existing categories or newly invented per the rules above).
- "subcategory": Specific niche/domain under this category (e.g. "Photos", "Video Editing", "Pentesting", "Audio Stem Separation").
- "tags": Array of 3-5 lowercase hashtags (e.g. ["photo-editing", "ai", "background-removal"]).
- "detailed_summary": 2-3 sentences explaining core capabilities, free vs paid tier, and notable features.
- "how_to_use": Actionable tips or exact commands on how to use it immediately.
- "safety_status": One of:
    * "SAFE" (Official platform, trusted open-source, or standard SaaS).
    * "PENTEST_ONLY" (Dual-use offensive security tool or scanner - only legal on authorized infrastructure).
    * "CAUTION" (Freemium with data privacy caveats or aggressive tracking).
    * "SUSPICIOUS" (Adware, piracy, or phishing risk).
- "safety_notes": 1 clear sentence explaining legality, compliance, or safety caution.

OUTPUT FORMAT:
Respond with a RAW JSON array of objects `[ {{...}}, {{...}} ]`. Output ZERO markdown fences, ZERO conversational intro."""


# Static prompt retained for backward-compatibility if referenced externally
SYSTEM_PROMPT = build_extraction_system_prompt()


def parse_and_enrich_text(raw_text: str, source_context: str = "Screenshot OCR", existing_categories: List[str] = None) -> List[Dict]:
    """Uses LLM to identify, categorize, and enrich all websites/tricks in text."""
    if not raw_text or len(raw_text.strip()) < 5:
        return []

    if existing_categories is None:
        existing_categories = get_existing_categories_list()

    system_prompt = build_extraction_system_prompt(existing_categories)

    user_prompt = f"""SOURCE CONTEXT: {source_context}
EXTRACTED CONTENT:
{raw_text[:4000]}

Extract all distinct websites, software tools, or practical tricks. If multiple tools are listed (e.g. '5 websites you must know'), return an entry for EACH ONE following the two-tier categorization rules.
Return strictly a valid JSON array."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    try:
        raw_output = call_llm(messages, max_tokens=1800, temperature=0.2)
        clean_json = re.sub(r'^```(?:json)?\s*', '', raw_output.strip())
        clean_json = re.sub(r'\s*```$', '', clean_json).strip()

        data = None
        # Attempt 1: direct parse
        try:
            data = json.loads(clean_json)
        except Exception:
            # Attempt 2: isolate array
            m = re.search(r'\[\s*\{.*\}\s*\]', clean_json, re.DOTALL)
            if m:
                try:
                    data = json.loads(m.group(0))
                except Exception:
                    pass

        # Attempt 3: parse individual JSON objects with regex
        if not data:
            objects = []
            for obj_str in re.findall(r'\{[^{}]*"title"[^{}]*\}', clean_json, re.DOTALL):
                try:
                    parsed_obj = json.loads(obj_str)
                    if isinstance(parsed_obj, dict) and parsed_obj.get("title"):
                        objects.append(parsed_obj)
                except Exception:
                    continue
            if objects:
                data = objects

        if not data:
            raise ValueError(f"No valid JSON structure found in LLM response: {raw_output[:120]}")

        if isinstance(data, dict):
            data = [data]
        elif not isinstance(data, list):
            data = []

        # Validate and sanitize categories with intelligent dynamic detection
        sanitized = []
        active_categories = list(existing_categories)
        for item in data:
            if not item.get("title"):
                continue
            raw_cat = item.get("category", "")
            raw_sub = item.get("subcategory", "")
            cat, subcat = normalize_category_and_subcategory(raw_cat, raw_sub, active_categories)
            item["category"] = cat
            item["subcategory"] = subcat
            if cat not in active_categories:
                active_categories.append(cat)

            if not item.get("safety_status"):
                item["safety_status"] = "SAFE"
            raw_url = str(item.get("url", "")).strip()
            item["url"] = raw_url if is_safe_url(raw_url) else ""
            sanitized.append(item)

        return sanitized
    except Exception as e:
        print(f"[warn] JSON parsing error in LLM extraction ({e})")
        fallback_cat, fallback_sub = normalize_category_and_subcategory("General Utilities", "Tools", existing_categories)
        return [{
            "title": "Extracted Note & Trick",
            "url": "",
            "one_liner": raw_text[:120].strip(),
            "category": fallback_cat,
            "subcategory": fallback_sub,
            "tags": ["notes", "tricks", "reference"],
            "detailed_summary": raw_text[:500],
            "how_to_use": "Refer to raw note.",
            "safety_status": "SAFE",
            "safety_notes": "User saved note."
        }]


# =====================================================================
# HIGH-LEVEL INGESTION ENTRYPOINTS
# =====================================================================

def process_image_upload(image_path: str) -> List[Dict]:
    """Ingests an image/screenshot, runs OCR, and enriches all detected tools."""
    print(f"[OmniVault] Processing image: {image_path}")
    ocr_text = ocr_image(image_path)
    if not ocr_text:
        ocr_text = Path(image_path).stem.replace("_", " ")

    results = parse_and_enrich_text(ocr_text, source_context="Screenshot / Photo OCR")
    for r in results:
        r["source_type"] = "IMAGE"
        r["image_path"] = image_path
    return results


def process_url_input(url: str) -> List[Dict]:
    """Crawls a URL and enriches it into a structured Vault record."""
    print(f"[OmniVault] Crawling URL: {url}")
    meta = crawl_url_metadata(url)
    combined = f"URL: {url}\nTitle: {meta.get('title')}\nDescription: {meta.get('description')}\nContent: {meta.get('body_snippet')}"
    results = parse_and_enrich_text(combined, source_context=f"Live Web Crawl of {url}")
    for r in results:
        r["source_type"] = "URL"
        if not r.get("url"):
            r["url"] = url
    return results


def process_pdf_upload(pdf_path: str) -> List[Dict]:
    """Extracts text from PDF cheatsheets/guides and parses all tools."""
    print(f"[OmniVault] Extracting PDF: {pdf_path}")
    text = extract_text_from_pdf(pdf_path)
    results = parse_and_enrich_text(text, source_context=f"PDF Document: {Path(pdf_path).name}")
    for r in results:
        r["source_type"] = "PDF"
    return results


def process_raw_text(text: str) -> List[Dict]:
    """Processes freeform user text, lists, or prompt notes."""
    results = parse_and_enrich_text(text, source_context="User Note / List")
    for r in results:
        r["source_type"] = "MANUAL"
    return results


# =====================================================================
# CONVERSATIONAL ASSISTANT ("ASK VAULT")
# =====================================================================

def query_vault_ai(user_question: str, saved_resources: List[Dict]) -> str:
    """
    Answers Arush's natural language queries using relevance-ranked stored database items.
    Example: 'Mujhe video editing ya audio clean karne ke liye kaun si site thi?'
    """
    # Extract meaningful query tokens for relevance ranking
    tokens = [t.lower() for t in re.findall(r'\b\w{3,}\b', user_question)]

    def score_resource(r: Dict) -> int:
        score = 0
        title_lower = (r.get("title") or "").lower()
        one_liner_lower = (r.get("one_liner") or "").lower()
        tags_lower = (str(r.get("tags")) or "").lower()
        category_lower = (r.get("category") or "").lower()
        summary_lower = (r.get("detailed_summary") or "").lower()

        for tok in tokens:
            if tok in title_lower:
                score += 5
            if tok in one_liner_lower:
                score += 3
            if tok in tags_lower:
                score += 3
            if tok in category_lower:
                score += 2
            if tok in summary_lower:
                score += 1
        return score

    # Rank resources by score (descending); prioritize matching items
    ranked = sorted(saved_resources, key=score_resource, reverse=True)
    matching = [r for r in ranked if score_resource(r) > 0]
    selected_resources = matching[:10] if matching else ranked[:5]

    res_summary = []
    for r in selected_resources:
        res_summary.append({
            "title": r.get("title"),
            "url": r.get("url"),
            "category": r.get("category"),
            "one_liner": r.get("one_liner"),
            "tags": r.get("tags"),
            "safety": r.get("safety_status")
        })

    prompt = f"""USER QUESTION:
{user_question}

SAVED RESOURCES IN ARUSH'S VAULT:
{json.dumps(res_summary, indent=2)}

INSTRUCTIONS:
1. Answer Arush directly in a friendly, high-energy student builder voice (Hinglish/English).
2. Recommend the exact matching tool(s) from his vault with their title, 1-line reason, and direct URL.
3. If multiple tools can do the job, briefly compare them in 1 sentence.
4. If NO tool in the vault matches what he wants, tell him candidly and recommend a top verified tool he can add right now."""

    messages = [
        {"role": "system", "content": "You are Arush's personal OmniVault Second-Brain Assistant."},
        {"role": "user", "content": prompt}
    ]

    try:
        return call_llm(messages, max_tokens=600, temperature=0.5)
    except Exception as e:
        return f"Error consulting OmniVault AI: {e}"


def search_vault(query: str, limit: int = 10) -> List[Dict]:
    """Fuzzy and keyword search across saved vault resources."""
    try:
        from .models import VaultResource
        from django.db.models import Q
        q_clean = query.strip()
        qs = VaultResource.objects.filter(
            Q(title__icontains=q_clean) |
            Q(one_liner__icontains=q_clean) |
            Q(category__icontains=q_clean) |
            Q(subcategory__icontains=q_clean) |
            Q(tags__icontains=q_clean) |
            Q(detailed_summary__icontains=q_clean) |
            Q(raw_ocr_text__icontains=q_clean)
        ).order_by('-favorite', '-created_at')[:limit]
        return [
            {
                "id": r.id,
                "title": r.title,
                "url": r.url,
                "category": r.category,
                "subcategory": r.subcategory,
                "one_liner": r.one_liner,
                "safety_status": r.safety_status,
                "favorite": r.favorite,
                "tags": r.tags
            }
            for r in qs
        ]
    except Exception:
        return []
