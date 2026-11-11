#!/usr/bin/env python3
"""
migrate_vault_categories.py — Re-evaluates and automatically categorizes all VaultResource records.
Guarantees Claude skills, agent skills, coding tools, security utilities, etc.
are neatly organized into dedicated categories rather than generic buckets.
"""

import os
import sys
from pathlib import Path

# Setup Django Environment
HUB_DIRS = [
    Path.home() / "omni_hub",
    Path("/home/arush/omni_hub"),
    Path(__file__).resolve().parent.parent / "omni_hub",
    Path("C:/Users/Arush/OneDrive/Documents/omni/omni_hub")
]

HUB_PATH = None
for d in HUB_DIRS:
    if d.exists() and (d / "manage.py").exists():
        HUB_PATH = d
        break

if not HUB_PATH:
    print("❌ omni_hub directory not found")
    sys.exit(1)

if str(HUB_PATH) not in sys.path:
    sys.path.insert(0, str(HUB_PATH))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "omni_hub.settings")

import django
django.setup()

from growth.models import VaultResource
from growth import omni_vault_engine
from django.db.models import Count

def run_migration():
    print("=" * 60)
    print("OMNIVAULT SMART CATEGORY MIGRATION & REORGANIZATION")
    print("=" * 60)

    # Initial counts
    print("\n[1] Initial Category Distribution:")
    before_counts = dict(
        VaultResource.objects.values_list('category')
        .annotate(total=Count('id'))
        .order_by('-total')
    )
    for cat, count in before_counts.items():
        print(f"    - {cat}: {count} items")

    # Process all resources
    updated_count = 0
    all_resources = list(VaultResource.objects.all())

    for r in all_resources:
        old_cat = r.category
        new_cat = omni_vault_engine.detect_smart_category(
            title=r.title,
            category_hint=r.category,
            subcategory=r.subcategory,
            tags=r.tags,
            text_context=f"{r.one_liner} {r.detailed_summary} {r.raw_ocr_text}"
        )

        # Additional cleanups for Claude skills
        tags_str = (r.tags or "").lower()
        title_lower = (r.title or "").lower()
        one_liner_lower = (r.one_liner or "").lower()

        if any(w in tags_str or w in title_lower or w in one_liner_lower for w in ["claude", "agent-skill", "agent skill", "coding-agent", "cursor"]):
            new_cat = "Claude & Agent Skills"

        if new_cat != old_cat:
            r.category = new_cat
            r.save()
            updated_count += 1
            print(f"  ⚡ [{r.id}] '{r.title}': '{old_cat}' -> '{new_cat}'")

    print(f"\n[2] Migration complete. Updated {updated_count} resource(s).")

    # Final counts
    print("\n[3] Final Category Distribution:")
    after_counts = dict(
        VaultResource.objects.values_list('category')
        .annotate(total=Count('id'))
        .order_by('-total')
    )
    for cat, count in after_counts.items():
        icon = omni_vault_engine.CATEGORY_ICONS.get(cat, "📁")
        print(f"    {icon} {cat}: {count} items")

    print("\n✅ All categories are now automatically organized and separated!")

if __name__ == "__main__":
    run_migration()
