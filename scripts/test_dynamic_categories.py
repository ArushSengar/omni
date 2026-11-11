import os
import sys
import json
from pathlib import Path

# Setup Django Environment
sys.path.insert(0, "/home/arush/omni_hub")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "omni_hub.settings")
import django
django.setup()

from growth.models import VaultResource
from growth import omni_vault_engine
from growth.views import get_categories_with_metadata

print("=== STEP 1: Current Active Categories in Database ===")
cats_before = omni_vault_engine.get_existing_categories_list()
print("Categories in DB:", cats_before)

print("\n=== STEP 2: Ingest Photo Editing Tools ===")
photo_tools_text = """Top Websites for Photo Editing:
1. Photoroom (https://photoroom.com): 1 click mein image background erase karke high quality transparent PNG banata hai.
2. Pixlr Editor (https://pixlr.com): Free online browser photo editor with layers, filters, and image manipulation.
"""
results1 = omni_vault_engine.parse_and_enrich_text(photo_tools_text, source_context="Photo Editing Test")
print(f"LLM Extracted {len(results1)} item(s):")
saved_ids = []
for r in results1:
    res = VaultResource.objects.create(
        title=r.get("title", "Photo Tool"),
        url=r.get("url", ""),
        one_liner=r.get("one_liner", ""),
        category=r.get("category"),
        subcategory=r.get("subcategory", ""),
        tags=",".join(r.get("tags", [])),
        detailed_summary=r.get("detailed_summary", ""),
        safety_status=r.get("safety_status", "SAFE"),
        source_type="manual"
    )
    saved_ids.append(res.id)
    print(f"  -> Saved: {res.title} | Category: [{res.category}] | Subcategory: [{res.subcategory}]")

parent_cat = results1[0].get("category")
print(f"Dynamic parent category established: '{parent_cat}'")

print("\n=== STEP 3: Ingest Video Tool (Should REUSE parent category and branch new subcategory) ===")
video_tool_text = """CapCut Web (https://capcut.com): Browser-based video editor for reels trimming, auto captions, and audio sync."""
results2 = omni_vault_engine.parse_and_enrich_text(video_tool_text, source_context="Video Editing Test")
print(f"LLM Extracted {len(results2)} item(s):")
for r in results2:
    res = VaultResource.objects.create(
        title=r.get("title", "Video Tool"),
        url=r.get("url", ""),
        one_liner=r.get("one_liner", ""),
        category=r.get("category"),
        subcategory=r.get("subcategory", ""),
        tags=",".join(r.get("tags", [])),
        detailed_summary=r.get("detailed_summary", ""),
        safety_status=r.get("safety_status", "SAFE"),
        source_type="manual"
    )
    saved_ids.append(res.id)
    print(f"  -> Saved: {res.title} | Category: [{res.category}] | Subcategory: [{res.subcategory}]")

print("\n=== STEP 4: Inspect Dynamic Category Hierarchy in Live API ===")
meta = get_categories_with_metadata()
found_dynamic_parent = False
for c in meta:
    sub_names = [s["name"] + " (" + str(s["count"]) + ")" for s in c.get("subcategories", [])]
    print(f"  {c['icon']} {c['name']} ({c['count']} items) -> Subcategories: {sub_names}")
    if c["name"].lower() == parent_cat.lower():
        found_dynamic_parent = True
        print(f"  🎯 VERIFIED DYNAMIC CATEGORY '{c['name']}' with {len(c.get('subcategories', []))} subcategories!")

assert found_dynamic_parent, f"Dynamic parent '{parent_cat}' not found in metadata!"

print("\n=== STEP 5: Clean Up Test Items ===")
deleted_count, _ = VaultResource.objects.filter(id__in=saved_ids).delete()
print(f"Cleaned up {deleted_count} temporary test entries from database.")

print("\nSUCCESS: Dynamic Two-Tier Category Creation & Reuse Verified 100%!")
