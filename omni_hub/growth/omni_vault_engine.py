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
from typing import List, Dict, Optional

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
    """Blocks private, loopback, link-local, reserved, multicast, and unspecified (0.0.0.0/::) IPs."""
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

CANONICAL_CATEGORIES = [
    "Claude & Agent Skills",
    "AI & LLM Tools",
    "Cyber Security & Pentesting",
    "Developer & APIs",
    "Linux, Homelab & Systems",
    "Media, Audio & Design",
    "Productivity & Automation",
    "Student & Learning"
]
VALID_CATEGORIES = CANONICAL_CATEGORIES

CATEGORY_ICONS = {
    "All": "🌐",
    "Claude & Agent Skills": "🤖",
    "AI & LLM Tools": "🧠",
    "Cyber Security & Pentesting": "🛡️",
    "Developer & APIs": "💻",
    "Linux, Homelab & Systems": "🐧",
    "Media, Audio & Design": "🎨",
    "Productivity & Automation": "⚡",
    "Student & Learning": "🎓",
    "Reverse Engineering": "🔍",
    "OSINT & Reconnaissance": "🕵️",
    "Web Scraping & Automation": "🕸️",
}

CATEGORY_FA_ICONS = {
    "All": "fa-layer-group",
    "Claude & Agent Skills": "fa-robot",
    "AI & LLM Tools": "fa-brain",
    "Cyber Security & Pentesting": "fa-shield-halved",
    "Developer & APIs": "fa-code",
    "Linux, Homelab & Systems": "fa-server",
    "Media, Audio & Design": "fa-palette",
    "Productivity & Automation": "fa-bolt",
    "Student & Learning": "fa-graduation-cap",
    "Reverse Engineering": "fa-magnifying-glass-chart",
    "OSINT & Reconnaissance": "fa-user-secret",
    "Web Scraping & Automation": "fa-spider",
}


def detect_smart_category(title: str = "", category_hint: str = "", subcategory: str = "", tags = None, text_context: str = "") -> str:
    """
    Intelligently determines and normalizes the precise category for a resource.
    Guarantees that Claude skills, agent skills, coding tools, security utilities, etc.
    are automatically placed into their clean, distinct categories rather than generic buckets.
    """
    tags_list = tags if isinstance(tags, list) else ([t.strip() for t in str(tags).split(",") if t.strip()] if tags else [])
    combined_search = " ".join([
        str(title or ""),
        str(category_hint or ""),
        str(subcategory or ""),
        " ".join(tags_list),
        str(text_context or "")
    ]).lower()

    # 1. Claude & Agent Skills
    # Covers Claude Code, Cursor, AI agents, MCP servers, prompt-engineering skills, and agent toolkits
    agent_keywords = [
        "claude", "claude-code", "claude code", "agent-skill", "agent-skills", "agent skill",
        "agent skills", "coding-agent", "coding agent", "cursor skill", "cursor rule",
        "mcp server", "mcp-server", "model context protocol", "agent architecture",
        "anti-slop", "anti-ai-slop", "skill card", "ai agent skill", "agent tool",
        "claude design", "hermes-agent", "hermes skill"
    ]
    if any(k in combined_search for k in agent_keywords):
        return "Claude & Agent Skills"

    # 2. Canonical or Category Hint Match
    if category_hint:
        clean_hint = category_hint.strip()
        for can in CANONICAL_CATEGORIES:
            if clean_hint.lower() == can.lower():
                return can
        hint_lower = clean_hint.lower()
        if "agent" in hint_lower or "claude" in hint_lower:
            return "Claude & Agent Skills"
        if "ai" in hint_lower or "llm" in hint_lower or "gpt" in hint_lower:
            return "AI & LLM Tools"
        if "security" in hint_lower or "pentest" in hint_lower or "osint" in hint_lower or "hack" in hint_lower:
            return "Cyber Security & Pentesting"
        if "linux" in hint_lower or "homelab" in hint_lower or "sysadmin" in hint_lower or "server" in hint_lower:
            return "Linux, Homelab & Systems"
        if "audio" in hint_lower or "media" in hint_lower or "video" in hint_lower or "design" in hint_lower:
            return "Media, Audio & Design"
        if "developer" in hint_lower or "api" in hint_lower or "sdk" in hint_lower:
            return "Developer & APIs"
        if "student" in hint_lower or "learn" in hint_lower or "career" in hint_lower or "interview" in hint_lower:
            return "Student & Learning"
        if "productivity" in hint_lower or "automation" in hint_lower or "workflow" in hint_lower:
            return "Productivity & Automation"

        # Allow well-formed custom category in Title Case
        if 2 <= len(clean_hint) <= 40 and not any(ch in clean_hint for ch in '{}[]<>;$"\\'):
            words = clean_hint.replace("_", " ").replace("-", " ").split()
            return " ".join(w.capitalize() if w.lower() not in ("and", "&", "of", "the", "in", "for") else w for w in words).strip()

    # 3. Context Heuristics Fallback
    if any(k in combined_search for k in ["pentest", "exploit", "cve", "malware", "ctf", "vulnerability", "nmap", "wireshark", "virustotal", "pwn", "osint"]):
        return "Cyber Security & Pentesting"
    if any(k in combined_search for k in ["homelab", "linux", "bash", "terminal", "docker", "systemd", "kernel", "pi4", "raspberry", "explainshell"]):
        return "Linux, Homelab & Systems"
    if any(k in combined_search for k in ["vocal", "stem-separation", "audio", "tinypng", "image-compression", "video-editor", "font", "color-palette", "lalal"]):
        return "Media, Audio & Design"
    if any(k in combined_search for k in ["interview", "dsa", "leetcode", "cheatsheet", "student", "placement", "course"]):
        return "Student & Learning"
    if any(k in combined_search for k in ["chatgpt", "gemini", "anthropic", "prompt", "fine-tuning", "rag", "embedding", "ollama", "local-llm"]):
        return "AI & LLM Tools"

    return "Developer & APIs"



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

SYSTEM_PROMPT = """You are OmniVault Intelligence, an expert digital knowledge extractor and research librarian built for Arush Sengar (Cyber Security student, builder, and homelab tinkerer).

Your job is to analyze raw input (OCR text from screenshots, web scrapes, PDF text, or user notes) and identify EVERY distinct website, utility, digital trick, or software tool mentioned.

FOR EACH TOOL / WEBSITE DETECTED, RETURN A STRICT JSON OBJECT WITH:
- "title": Clean canonical name (e.g. "CyberChef", "v0.dev", "LALAL.AI", "Explainshell").
- "url": Real canonical URL (e.g. "https://gchq.github.io/CyberChef/"). If not explicit, deduce the official domain.
- "one_liner": A punchy, crystal-clear 1-sentence explanation in simple Hindi/English student-friendly language explaining EXACTLY what this tool does and what it is used for (e.g. "1 click mein audio se vocal aur background music alag karne ke liye" or "Linux terminal commands ke flags ko visual breakdown ke saath explain karne ke liye"). NEVER use generic corporate fluff.
- "category": MUST be the most precise, accurate technical category. Standard categories include:
    * "Claude & Agent Skills" (ALL Claude Code skills, Cursor rules, AI coding agents, autonomous agent workflows, MCP tools, and agent skill cards. e.g. REA, Ponytail, Hallmark, Impeccable, Diagram Design for Claude, Humanizer, agent prompt packs).
    * "AI & LLM Tools" (General LLM models, RAG engines, enterprise search, AI chat interfaces).
    * "Cyber Security & Pentesting" (Offensive security, CTF, network tools, scanners, OSINT, reverse engineering).
    * "Developer & APIs" (SDKs, APIs, HTTP tools, software libraries, web utilities).
    * "Linux, Homelab & Systems" (Linux commands, homelab servers, systemd, docker, CLI tools).
    * "Media, Audio & Design" (Audio stem separation, image compression, video, UI design).
    * "Productivity & Automation" (Workflow automation, browser helpers, notes).
    * "Student & Learning" (Interview prep, DSA, placement cheatsheets, documentation).
    * OR a clean, concise custom category in Title Case (e.g. "Web Scraping & Stealth") if none of the above fit accurately.
- "subcategory": Specific domain (e.g. "Audio Separation", "Linux Hardening", "UI Mockup").
- "tags": Array of 3-5 lowercase hashtags (e.g. ["audio", "ai", "free", "stem-separation"]).
- "detailed_summary": 2-3 sentences explaining core capabilities, free vs paid tier, and notable features.
- "how_to_use": Actionable tips or exact commands on how to use it immediately.
- "safety_status": One of:
    * "SAFE" (Official platform, trusted open-source, or standard SaaS).
    * "PENTEST_ONLY" (Dual-use offensive security tool or scanner - only legal on authorized infrastructure).
    * "CAUTION" (Freemium with data privacy caveats or aggressive tracking).
    * "SUSPICIOUS" (Adware, piracy, or phishing risk).
- "safety_notes": 1 clear sentence explaining legality, compliance, or safety caution.

OUTPUT FORMAT:
Respond with a RAW JSON array of objects `[ {...}, {...} ]`. Output ZERO markdown fences, ZERO conversational intro."""


def parse_and_enrich_text(raw_text: str, source_context: str = "Screenshot OCR") -> List[Dict]:
    """Uses LLM to identify, categorize, and enrich all websites/tricks in text."""
    if not raw_text or len(raw_text.strip()) < 5:
        return []

    user_prompt = f"""SOURCE CONTEXT: {source_context}
EXTRACTED CONTENT:
{raw_text[:4000]}

Extract all distinct websites, software tools, or practical tricks. If multiple tools are listed (e.g. '5 websites you must know'), return an entry for EACH ONE.
Return strictly a valid JSON array."""

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
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


        # Validate and sanitize categories with intelligent automatic detection
        sanitized = []
        for item in data:
            if not item.get("title"):
                continue
            cat = detect_smart_category(
                title=item.get("title", ""),
                category_hint=item.get("category", ""),
                subcategory=item.get("subcategory", ""),
                tags=item.get("tags", []),
                text_context=raw_text
            )
            item["category"] = cat
            if not item.get("safety_status"):
                item["safety_status"] = "SAFE"
            raw_url = str(item.get("url", "")).strip()
            item["url"] = raw_url if is_safe_url(raw_url) else ""
            sanitized.append(item)

        return sanitized
    except Exception as e:
        print(f"[warn] JSON parsing error in LLM extraction ({e})")
        fallback_cat = detect_smart_category(text_context=raw_text)
        # Fallback single item
        return [{
            "title": "Extracted Note & Trick",
            "url": "",
            "one_liner": raw_text[:120].strip(),
            "category": fallback_cat,
            "subcategory": "General Utilities",
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
                "one_liner": r.one_liner,
                "safety_status": r.safety_status,
                "favorite": r.favorite,
                "tags": r.tags
            }
            for r in qs
        ]
    except Exception:
        return []
