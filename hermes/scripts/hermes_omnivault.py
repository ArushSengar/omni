#!/usr/bin/env python3
"""
hermes_omnivault.py — Universal Bridge between Hermes AI Agent & OmniVault / Omni Hub.
Author: Arush Sengar

Empowers Hermes to autonomously:
1. Ingest images/screenshots directly into OmniVault with OCR, AI categorization, and 1-line purpose summaries.
2. Ingest URLs and technical notes without opening a web browser.
3. Query stored knowledge ("Hermes, mujhe audio split karne wali site batao jo save ki thi").
4. Inspect AI Wallet quotas and Pi system telemetry.

CLI Usage:
  hermes-omnivault ingest-image /path/to/screenshot.png
  hermes-omnivault ingest-url https://example.com/tool
  hermes-omnivault ingest-note "CyberChef recipe for base64 decode" --title "CyberChef Base64"
  hermes-omnivault search "OSINT tools"
  hermes-omnivault wallet
  hermes-omnivault status
"""

import os
import sys
import json
import argparse
import urllib.request
import urllib.parse
from pathlib import Path

# Setup Django Environment for Direct Database Access
HUB_DIRS = [
    Path.home() / "omni_hub",
    Path("/home/arush/omni_hub"),
    Path(__file__).resolve().parent.parent.parent / "omni_hub",
    Path("C:/Users/Arush/OneDrive/Documents/omni/omni_hub")
]

HUB_PATH = None
for d in HUB_DIRS:
    if d.exists() and (d / "manage.py").exists():
        HUB_PATH = d
        break

if HUB_PATH:
    if str(HUB_PATH) not in sys.path:
        sys.path.insert(0, str(HUB_PATH))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "omni_hub.settings")
    try:
        import django
        django.setup()
        from growth.models import VaultResource
        from growth import omni_vault_engine
        DJANGO_AVAILABLE = True
    except Exception as e:
        DJANGO_AVAILABLE = False
        _DJANGO_ERR = str(e)
else:
    DJANGO_AVAILABLE = False
    _DJANGO_ERR = "omni_hub directory not found"


def format_output(data: dict, as_json: bool = False):
    """Prints output either as clean JSON (for programmatic Hermes agent consumption) or human-readable text."""
    if as_json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        status = data.get("status", "info")
        if status == "ok" or status == "saved":
            print(f"✅ {data.get('message', 'Operation successful')}")
            if "resource" in data:
                r = data["resource"]
                sub = f" // {r.get('subcategory')}" if r.get('subcategory') else ""
                print(f"   📌 Title:    {r.get('title')}")
                print(f"   📂 Category: {r.get('category')}{sub}")
                print(f"   💡 Purpose:  {r.get('one_liner')}")
                print(f"   🛡️ Safety:   {r.get('safety_status', 'SAFE')}")
                if r.get("url"):
                    print(f"   🔗 Link:     {r.get('url')}")
            elif "results" in data:
                print(f"Found {len(data['results'])} matching resources:")
                for idx, item in enumerate(data["results"], 1):
                    fav = "⭐ " if item.get("favorite") else ""
                    sub = f" // {item.get('subcategory')}" if item.get('subcategory') else ""
                    print(f"\n   [{idx}] {fav}{item.get('title')} ({item.get('category')}{sub})")
                    print(f"       Purpose: {item.get('one_liner')}")
                    if item.get("url"):
                        print(f"       Link:    {item.get('url')}")
            elif "wallet" in data:
                w = data["wallet"]
                print(f"   💳 Active Providers: {w.get('active_providers')}/{w.get('total_providers')}")
                print(f"   💰 Total Cost Saved: ${w.get('cost_saved_usd', 0.0)}")
                tokens = w.get('tokens_processed', w.get('monthly_tokens', 0))
                print(f"   ⚡ Monthly Tokens:   {tokens:,}")
            elif "system" in data:
                s = data["system"]
                print(f"   🌡️ Temp:   {s.get('temp_c')}°C")
                print(f"   🧠 RAM:    {s.get('memory', {}).get('percent')}% (Free: {s.get('memory', {}).get('free_mb')}MB)")
                print(f"   💾 Disk:   {s.get('disk', {}).get('free_gb')}GB free")
                print(f"   ⏱️ Uptime: {s.get('uptime')}")
        else:
            print(f"❌ Error: {data.get('message', 'Unknown failure')}")


def ingest_image(image_path: str, title: str = None, category: str = None, as_json: bool = False):
    """Processes an image, extracts text via OCR, decomposes tools via AI, and saves into OmniVault."""
    p = Path(image_path)
    if not p.exists():
        format_output({"status": "error", "message": f"Image file not found at: {image_path}"}, as_json)
        return False

    if not DJANGO_AVAILABLE:
        format_output({"status": "error", "message": f"Django ORM unavailable: {_DJANGO_ERR}"}, as_json)
        return False

    try:
        # 1. OCR Extraction
        ocr_text = omni_vault_engine.ocr_image(str(p))
        if not ocr_text or len(ocr_text.strip()) < 5:
            ocr_text = f"Visual reference saved from file: {p.name}"

        # 2. AI Tool Extraction & Synthesis
        tools = omni_vault_engine.parse_and_enrich_text(ocr_text, source_context=f"Hermes Image Ingest: {p.name}")
        if not tools:
            # Fallback if text is sparse
            tools = [{
                "title": title or p.stem.replace("_", " ").replace("-", " ").title(),
                "url": "",
                "one_liner": "Visual trick or tool captured via Hermes Agent.",
                "category": category or "Developer & APIs",
                "subcategory": "Visual Ingest",
                "tags": ["hermes-ingest", "screenshot"],
                "detailed_summary": ocr_text[:500],
                "safety_status": "SAFE"
            }]

        saved_records = []
        from django.db import transaction
        with transaction.atomic():
            for t in tools:
                if title:
                    t["title"] = title
                if category:
                    t["category"] = category

                raw_url = str(t.get("url", "")).strip()
                safe_url = raw_url if omni_vault_engine.is_safe_url(raw_url) else ""

                tags = t.get("tags", [])
                tags_str = ",".join(tags) if isinstance(tags, list) else str(tags)

                cat = omni_vault_engine.detect_smart_category(
                    title=t.get("title", p.stem),
                    category_hint=category or t.get("category", ""),
                    subcategory=t.get("subcategory", ""),
                    tags=tags,
                    text_context=ocr_text
                )

                res = VaultResource.objects.create(
                    title=t.get("title", p.stem),
                    url=safe_url,
                    one_liner=t.get("one_liner", "Useful tool or trick"),
                    category=cat,
                    subcategory=t.get("subcategory", ""),
                    tags=tags_str,
                    detailed_summary=t.get("detailed_summary", ""),
                    how_to_use=t.get("how_to_use", ""),
                    safety_status=t.get("safety_status", "SAFE"),
                    safety_notes=t.get("safety_notes", ""),
                    source_type="screenshot",
                    raw_ocr_text=ocr_text[:3000],
                    image_path=p.name
                )
                saved_records.append({
                    "id": res.id,
                    "title": res.title,
                    "url": res.url,
                    "category": res.category,
                    "subcategory": res.subcategory,
                    "one_liner": res.one_liner,
                    "safety_status": res.safety_status
                })

        format_output({
            "status": "saved",
            "message": f"Successfully ingested image into OmniVault ({len(saved_records)} tool(s) registered)",
            "resource": saved_records[0] if saved_records else {},
            "all_resources": saved_records
        }, as_json)
        return True

    except Exception as e:
        format_output({"status": "error", "message": f"Ingestion failed: {e}"}, as_json)
        return False


def ingest_url(url: str, category: str = None, as_json: bool = False):
    """Crawls URL metadata, analyzes legality & category, and persists to OmniVault."""
    if not DJANGO_AVAILABLE:
        format_output({"status": "error", "message": f"Django ORM unavailable: {_DJANGO_ERR}"}, as_json)
        return False

    if not omni_vault_engine.is_safe_url(url):
        format_output({"status": "error", "message": f"Security restriction: URL {url} is restricted or private."}, as_json)
        return False

    try:
        meta = omni_vault_engine.crawl_url_metadata(url)
        if "error" in meta and not meta.get("title"):
            format_output({"status": "error", "message": f"URL crawl blocked or failed: {meta['error']}"}, as_json)
            return False

        combined = f"Title: {meta.get('title')}\nDescription: {meta.get('description')}\nSnippet:\n{meta.get('body_snippet', '')}"

        tools = omni_vault_engine.parse_and_enrich_text(combined, source_context=f"Hermes URL Ingest: {url}")
        if not tools:
            tools = [{
                "title": meta.get("title") or url,
                "url": url,
                "one_liner": meta.get("description") or "Useful online resource",
                "category": category or "Developer & APIs",
                "safety_status": "SAFE"
            }]

        saved = []
        from django.db import transaction
        with transaction.atomic():
            for t in tools:
                raw_url = str(t.get("url") or url).strip()
                safe_url = raw_url if omni_vault_engine.is_safe_url(raw_url) else ""

                tags = t.get("tags", [])
                tags_str = ",".join(tags) if isinstance(tags, list) else str(tags)

                cat = omni_vault_engine.detect_smart_category(
                    title=t.get("title") or meta.get("title") or url,
                    category_hint=category or t.get("category", ""),
                    subcategory=t.get("subcategory", ""),
                    tags=tags,
                    text_context=combined
                )

                res = VaultResource.objects.create(
                    title=t.get("title") or meta.get("title") or url,
                    url=safe_url,
                    one_liner=t.get("one_liner") or meta.get("description") or "Useful online tool",
                    category=cat,
                    subcategory=t.get("subcategory", ""),
                    tags=tags_str,
                    detailed_summary=t.get("detailed_summary") or meta.get("description", ""),
                    safety_status=t.get("safety_status", "SAFE"),
                    source_type="url",
                    raw_ocr_text=combined[:3000]
                )
                saved.append({
                    "id": res.id,
                    "title": res.title,
                    "url": res.url,
                    "category": res.category,
                    "subcategory": res.subcategory,
                    "one_liner": res.one_liner,
                    "safety_status": res.safety_status
                })

        format_output({
            "status": "saved",
            "message": "Successfully ingested URL into OmniVault",
            "resource": saved[0] if saved else {},
            "all_resources": saved
        }, as_json)
        return True

    except Exception as e:
        format_output({"status": "error", "message": f"URL ingest failed: {e}"}, as_json)
        return False


def ingest_note(text: str, title: str = None, category: str = None, as_json: bool = False):
    """Decomposes raw technical notes or cheatsheet snippets and saves into OmniVault."""
    if not DJANGO_AVAILABLE:
        format_output({"status": "error", "message": f"Django ORM unavailable: {_DJANGO_ERR}"}, as_json)
        return False

    try:
        tools = omni_vault_engine.parse_and_enrich_text(text, source_context="Hermes Technical Note")
        if not tools:
            tools = [{
                "title": title or "Technical Trick / Note",
                "url": "",
                "one_liner": text.split("\n")[0][:120],
                "category": category or "Developer & APIs",
                "safety_status": "SAFE"
            }]

        saved = []
        from django.db import transaction
        with transaction.atomic():
            for t in tools:
                if title:
                    t["title"] = title
                if category:
                    t["category"] = category

                tags = t.get("tags", [])
                tags_str = ",".join(tags) if isinstance(tags, list) else str(tags)

                cat = omni_vault_engine.detect_smart_category(
                    title=t.get("title", "Technical Note"),
                    category_hint=category or t.get("category", ""),
                    subcategory=t.get("subcategory", ""),
                    tags=tags,
                    text_context=text
                )

                res = VaultResource.objects.create(
                    title=t.get("title", "Technical Note"),
                    url=t.get("url", ""),
                    one_liner=t.get("one_liner", "Useful note or trick"),
                    category=cat,
                    subcategory=t.get("subcategory", ""),
                    tags=tags_str,
                    detailed_summary=text[:2000],
                    safety_status=t.get("safety_status", "SAFE"),
                    source_type="manual",
                    raw_ocr_text=text[:3000]
                )
                saved.append({
                    "id": res.id,
                    "title": res.title,
                    "category": res.category,
                    "subcategory": res.subcategory,
                    "one_liner": res.one_liner
                })

        format_output({
            "status": "saved",
            "message": "Successfully saved note into OmniVault",
            "resource": saved[0] if saved else {}
        }, as_json)
        return True

    except Exception as e:
        format_output({"status": "error", "message": f"Note ingest failed: {e}"}, as_json)
        return False


def search_vault(query: str, limit: int = 5, as_json: bool = False):
    """Searches stored resources across title, category, description, and OCR keywords."""
    if not DJANGO_AVAILABLE:
        format_output({"status": "error", "message": f"Django ORM unavailable: {_DJANGO_ERR}"}, as_json)
        return False

    try:
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

        results = []
        for r in qs:
            results.append({
                "id": r.id,
                "title": r.title,
                "url": r.url,
                "category": r.category,
                "subcategory": r.subcategory,
                "one_liner": r.one_liner,
                "safety_status": r.safety_status,
                "favorite": r.favorite,
                "tags": r.tags
            })

        format_output({
            "status": "ok",
            "query": query,
            "count": len(results),
            "results": results
        }, as_json)
        return True
    except Exception as e:
        format_output({"status": "error", "message": f"Vault search failed: {e}"}, as_json)
        return False


def get_wallet_stats(as_json: bool = False):
    """Retrieves AI Wallet quotas, active providers, and dollar savings."""
    try:
        from growth.views import get_wallet_stats as fetch_wallet
        w = fetch_wallet()
        format_output({"status": "ok", "wallet": w}, as_json)
        return True
    except Exception as e:
        format_output({"status": "error", "message": f"Failed to retrieve wallet stats: {e}"}, as_json)
        return False


def get_hub_status(as_json: bool = False):
    """Retrieves Raspberry Pi hardware health, CPU temp, RAM, Disk, and uptime."""
    try:
        from growth.views import get_system_metrics
        m = get_system_metrics()
        format_output({"status": "ok", "system": m}, as_json)
        return True
    except Exception as e:
        format_output({"status": "error", "message": f"Failed to retrieve system status: {e}"}, as_json)
        return False


def main():
    parser = argparse.ArgumentParser(description="Hermes <-> OmniVault Multimodal Memory Bridge")
    subparsers = parser.add_subparsers(dest="command")

    # Ingest Image
    p_img = subparsers.add_parser("ingest-image", help="Ingest screenshot or photo into OmniVault")
    p_img.add_argument("path", help="Path to image file")
    p_img.add_argument("--title", help="Optional explicit title")
    p_img.add_argument("--category", help="Optional category")
    p_img.add_argument("--json", action="store_true", help="Output as JSON")

    # Ingest URL
    p_url = subparsers.add_parser("ingest-url", help="Crawl and ingest URL into OmniVault")
    p_url.add_argument("url", help="Target website URL")
    p_url.add_argument("--category", help="Optional category")
    p_url.add_argument("--json", action="store_true", help="Output as JSON")

    # Ingest Note
    p_note = subparsers.add_parser("ingest-note", help="Ingest technical note or snippet into OmniVault")
    p_note.add_argument("text", help="Note content")
    p_note.add_argument("--title", help="Optional note title")
    p_note.add_argument("--category", help="Optional category")
    p_note.add_argument("--json", action="store_true", help="Output as JSON")

    # Search
    p_search = subparsers.add_parser("search", help="Search OmniVault resources")
    p_search.add_argument("query", help="Keywords or natural language search query")
    p_search.add_argument("--limit", type=int, default=5, help="Max results to return")
    p_search.add_argument("--json", action="store_true", help="Output as JSON")

    # Wallet
    p_wallet = subparsers.add_parser("wallet", help="Inspect AI Wallet quotas and savings")
    p_wallet.add_argument("--json", action="store_true", help="Output as JSON")

    # Status
    p_status = subparsers.add_parser("status", help="Inspect Pi hardware health and metrics")
    p_status.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    if args.command == "ingest-image":
        ingest_image(args.path, title=args.title, category=args.category, as_json=args.json)
    elif args.command == "ingest-url":
        ingest_url(args.url, category=args.category, as_json=args.json)
    elif args.command == "ingest-note":
        ingest_note(args.text, title=args.title, category=args.category, as_json=args.json)
    elif args.command == "search":
        search_vault(args.query, limit=args.limit, as_json=args.json)
    elif args.command == "wallet":
        get_wallet_stats(as_json=args.json)
    elif args.command == "status":
        get_hub_status(as_json=args.json)
    else:
        parser.print_help()


if __name__ == "__main__":
    try:
        main()
    finally:
        if DJANGO_AVAILABLE:
            try:
                from django.db import connections
                connections.close_all()
            except Exception:
                pass


