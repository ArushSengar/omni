#!/usr/bin/env python3
"""
vault_ingest.py — CLI Ingestion & Retrieval Tool for OmniVault.
Author: Arush Sengar

Allows Arush or Hermes agents to quickly ingest screenshots, URLs, notes, or PDFs,
or query stored knowledge directly from the terminal or Telegram.

Usage:
  python3 vault_ingest.py --image /path/to/screenshot.png
  python3 vault_ingest.py --url https://cyberchef.org
  python3 vault_ingest.py --text "Explainshell.com helps debug bash flags"
  python3 vault_ingest.py --pdf /path/to/cheatsheet.pdf
  python3 vault_ingest.py --query "Mujhe audio background remove karne wali site batao"
  python3 vault_ingest.py --list
"""

import os
import sys
import argparse
import json
import sqlite3
from pathlib import Path

# Setup Django Environment if running standalone
BASE_DIR = Path(__file__).resolve().parent
HUB_DIR = Path.home() / "omni_hub" if (Path.home() / "omni_hub").exists() else BASE_DIR

for p in [str(BASE_DIR), str(HUB_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "omni_hub.settings")

try:
    import django
    django.setup()
    from growth.models import VaultResource
    from growth import omni_vault_engine
    DJANGO_READY = True
except Exception as e:
    DJANGO_READY = False
    print(f"[warn] Django ORM initialization note: {e}")


def save_vault_resource(tool_data: dict, source_type: str, raw_text: str = "", image_path: str = "") -> VaultResource:
    """Helper to persist an enriched tool dictionary into VaultResource ORM with safe URLs."""
    tags = tool_data.get("tags", [])
    tags_str = ",".join(tags) if isinstance(tags, list) else str(tags)
    raw_url = str(tool_data.get("url", "")).strip()
    safe_url = raw_url if omni_vault_engine.is_safe_url(raw_url) else ""
    cat = omni_vault_engine.detect_smart_category(
        title=tool_data.get("title", ""),
        category_hint=tool_data.get("category", ""),
        subcategory=tool_data.get("subcategory", ""),
        tags=tags,
        text_context=raw_text
    )
    return VaultResource.objects.create(
        title=tool_data.get("title", "Tool"),
        url=safe_url,
        one_liner=tool_data.get("one_liner", "Useful tool or trick"),
        category=cat,
        subcategory=tool_data.get("subcategory", ""),
        tags=tags_str,
        detailed_summary=tool_data.get("detailed_summary", ""),
        how_to_use=tool_data.get("how_to_use", ""),
        safety_status=tool_data.get("safety_status", "SAFE"),
        safety_notes=tool_data.get("safety_notes", ""),
        source_type=source_type,
        raw_ocr_text=raw_text[:3000],
        image_path=str(image_path) if image_path else ""
    )


def ingest_image_cli(img_path: str):
    if not os.path.exists(img_path):
        print(f"❌ Error: Image file not found at {img_path}")
        return

    print(f"📷 Processing image OCR with Tesseract: {img_path}")
    ocr_text = omni_vault_engine.ocr_image(img_path)
    print(f"   Extracted {len(ocr_text)} characters.")

    print("🧠 Analyzing & decomposing tools with OmniRoute LLM...")
    tools = omni_vault_engine.parse_and_enrich_text(ocr_text, source_context=f"CLI Image Ingest: {Path(img_path).name}")
    print(f"   Discovered {len(tools)} distinct tool(s)!")

    for t in tools:
        res = save_vault_resource(t, source_type="screenshot", raw_text=ocr_text, image_path=str(img_path))
        sub = f" // {res.subcategory}" if res.subcategory else ""
        print(f"\n   ✅ SAVED: {res.title} [{res.category}{sub}]")
        print(f"      Target: {res.url or 'N/A'}")
        print(f"      Purpose: {res.one_liner}")
        print(f"      Safety: {res.safety_status}")


def ingest_url_cli(url: str):
    print(f"🌐 Crawling metadata for URL: {url}")
    meta = omni_vault_engine.crawl_url_metadata(url)
    combined = f"Title: {meta.get('title')}\nDescription: {meta.get('description')}\nSnippet:\n{meta.get('body_snippet', '')}"

    print("🧠 Synthesizing technical purpose with OmniRoute...")
    tools = omni_vault_engine.parse_and_enrich_text(combined, source_context=f"CLI URL: {url}")
    if not tools:
        tools = [{
            "title": meta.get("title") or url,
            "url": url,
            "one_liner": meta.get("description") or "Useful online resource",
            "category": "Developer & APIs",
            "safety_status": "SAFE"
        }]

    for t in tools:
        res = save_vault_resource(t, source_type="url", raw_text=combined)
        sub = f" // {res.subcategory}" if res.subcategory else ""
        print(f"\n   ✅ SAVED: {res.title} [{res.category}{sub}]")
        print(f"      URL: {res.url}")
        print(f"      Purpose: {res.one_liner}")


def ingest_text_cli(text: str):
    print("📝 Parsing input text and decomposing tools...")
    tools = omni_vault_engine.parse_and_enrich_text(text, source_context="CLI Notes")
    for t in tools:
        res = save_vault_resource(t, source_type="manual", raw_text=text)
        sub = f" // {res.subcategory}" if res.subcategory else ""
        print(f"\n   ✅ SAVED: {res.title} [{res.category}{sub}]")
        print(f"      Purpose: {res.one_liner}")


def ingest_pdf_cli(pdf_path: str):
    if not os.path.exists(pdf_path):
        print(f"❌ Error: Document or PDF file not found at {pdf_path}")
        return

    file_name = Path(pdf_path).name
    print(f"📄 Extracting text from document: {pdf_path}")
    text = omni_vault_engine.extract_text_from_document(pdf_path)
    if not text:
        # Direct read fallback
        try:
            with open(pdf_path, 'r', encoding='utf-8', errors='replace') as f:
                text = f.read()
        except Exception:
            pass

    if not text:
        print(f"❌ Error: Could not extract readable text from {pdf_path}")
        return
    print(f"   Extracted {len(text)} characters across document.")

    is_blueprint = any(k in file_name.lower() for k in ["blueprint", "arch", "roadmap", "spec", "plan"]) or \
                   any(k in text[:1000].lower() for k in ["blueprint", "architecture", "system design"])

    primary_title = Path(pdf_path).stem.replace("_", " ").replace("-", " ").title()
    for line in text.splitlines()[:15]:
        cl = line.strip()
        if cl.startswith("# ") and len(cl) > 3:
            primary_title = cl[2:].strip()
            break

    print("🧠 Analyzing & decomposing tools with OmniRoute LLM...")
    tools = []
    try:
        tools = omni_vault_engine.parse_and_enrich_text(text, source_context=f"CLI Document Ingest: {file_name}")
    except Exception as e:
        print(f"   [warn] LLM enrichment error: {e}")

    has_primary = any(t.get("title", "").strip().lower() == primary_title.lower() for t in tools)
    if not has_primary:
        doc_snippet = ""
        for line in text.splitlines()[:25]:
            cl = line.strip()
            if cl and not cl.startswith("#") and not cl.startswith("```") and len(cl) > 15:
                doc_snippet = cl[:220]
                break
        if not doc_snippet:
            doc_snippet = f"Technical document and blueprint for {primary_title}."

        primary_cat = "Blueprints & Architecture" if is_blueprint else "Student & Learning"
        primary_subcat = "System Architecture" if is_blueprint else "Guides & Documentation"

        primary_item = {
            "title": primary_title,
            "url": "",
            "one_liner": doc_snippet,
            "category": primary_cat,
            "subcategory": primary_subcat,
            "tags": ["blueprint", "architecture"] if is_blueprint else ["document"],
            "detailed_summary": text[:1200],
            "how_to_use": f"Refer to {primary_title} for architecture specifications and implementation details.",
            "safety_status": "SAFE",
            "safety_notes": "Internal technical reference and blueprint."
        }
        tools.insert(0, primary_item)

    print(f"   Discovered {len(tools)} structured item(s)!")

    for t in tools:
        res = save_vault_resource(t, source_type="pdf" if file_name.lower().endswith(".pdf") else "doc", raw_text=text)
        sub = f" // {res.subcategory}" if res.subcategory else ""
        print(f"\n   ✅ SAVED: {res.title} [{res.category}{sub}]")
        print(f"      Target: {res.url or 'N/A'}")
        print(f"      Purpose: {res.one_liner}")
        print(f"      Safety: {res.safety_status}")


def query_cli(q: str):
    print(f"🔍 Searching OmniVault for: '{q}'...")
    all_resources = list(VaultResource.objects.all()[:150].values(
        "id", "title", "url", "one_liner", "category", "subcategory", "tags", "safety_status", "how_to_use"
    ))
    ans = omni_vault_engine.query_vault_ai(q, all_resources)
    print("\n" + "=" * 60)
    print("🤖 OMNIVAULT AI RECOMMENDATION:")
    print("=" * 60)
    print(ans)
    print("=" * 60)


def list_cli():
    items = VaultResource.objects.all()
    print(f"\n📚 OmniVault Stored Resources ({items.count()} total):")
    print("-" * 75)
    for i in items:
        star = "★" if i.favorite else " "
        cat_disp = f"{i.category} // {i.subcategory}" if i.subcategory else i.category
        print(f"{star} [{i.safety_status:^12}] {i.title:<24} | {cat_disp:<30}")
        print(f"    ↳ {i.one_liner}")
        if i.url:
            print(f"    ↳ {i.url}")
        print()


def main():
    parser = argparse.ArgumentParser(description="OmniVault Multimodal Ingestion & Query CLI")
    parser.add_argument("--image", help="Path to image or screenshot to OCR and decompose")
    parser.add_argument("--url", help="Web URL to crawl and index")
    parser.add_argument("--text", help="Raw text notes or list of tools to parse")
    parser.add_argument("--pdf", help="Path to PDF document to index")
    parser.add_argument("--query", "-q", help="Ask Vault Assistant a question in Hindi or English")
    parser.add_argument("--list", action="store_true", help="List all stored resources")
    args = parser.parse_args()

    if not DJANGO_READY:
        sys.exit("Error: Could not initialize Django environment.")

    if args.image:
        ingest_image_cli(args.image)
    elif args.url:
        ingest_url_cli(args.url)
    elif args.text:
        ingest_text_cli(args.text)
    elif args.pdf:
        ingest_pdf_cli(args.pdf)
    elif args.query:
        query_cli(args.query)
    elif args.list:
        list_cli()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
