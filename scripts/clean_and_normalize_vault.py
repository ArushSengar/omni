import os
import sys
from pathlib import Path

# Setup Django Environment locally or on Pi
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
from django.db.models import Count

def migrate():
    print("=== 1. REMOVING EXACT DUPLICATES ===")
    # Duplicates of TryHackMe: keep latest, remove others
    thm_items = list(VaultResource.objects.filter(title="TryHackMe").order_by('-id'))
    if len(thm_items) > 1:
        for extra in thm_items[1:]:
            print(f"Deleting duplicate TryHackMe ID {extra.id}...")
            extra.delete()

    # Duplicates of CyberChef
    cc_items = list(VaultResource.objects.filter(title="CyberChef").order_by('id'))
    if len(cc_items) > 1:
        for extra in cc_items[1:]:
            print(f"Deleting duplicate CyberChef ID {extra.id}...")
            extra.delete()

    # Duplicates of Explainshell
    es_items = list(VaultResource.objects.filter(title__icontains="Explainshell").order_by('id'))
    if len(es_items) > 1:
        for extra in es_items[1:]:
            print(f"Deleting duplicate Explainshell ID {extra.id}...")
            extra.delete()

    # Duplicates of LALAL.AI
    lalal_items = list(VaultResource.objects.filter(title="LALAL.AI").order_by('id'))
    if len(lalal_items) > 1:
        for extra in lalal_items[1:]:
            print(f"Deleting duplicate LALAL.AI ID {extra.id}...")
            extra.delete()

    print("\n=== 2. NORMALIZING CLAUDE SKILLS ===")
    claude_skills = VaultResource.objects.filter(category__icontains="Claude")
    print(f"Found {claude_skills.count()} Claude skill items.")
    for item in claude_skills:
        item.category = "Claude Skills"
        item.subcategory = ""  # No micro-subcategories per user instruction!
        item.save()

    print("\n=== 3. CONSOLIDATING CYBER SECURITY SUBCATEGORIES ===")
    sec_items = VaultResource.objects.filter(category__icontains="Cyber Security")
    for item in sec_items:
        item.category = "Cyber Security & Pentesting"
        t = (item.title or "").lower()
        s = (item.subcategory or "").lower()
        
        if any(k in t or k in s for k in ["autopsy", "forensic", "volatility", "ftk", "steghide", "server forensics", "memory forensics"]):
            item.subcategory = "Forensics & Analysis"
        elif any(k in t or k in s for k in ["tryhackme", "hackthebox", "blue team labs", "learning platform", "training platform"]):
            item.subcategory = "Labs & Training"
        elif any(k in t or k in s for k in ["osint", "fingerprint", "behindthemail", "recon"]):
            item.subcategory = "OSINT & Recon"
        else:
            item.subcategory = "Security Tools"
        item.save()

    print("\n=== 4. CLEARING MICRO-SUBCATEGORIES FOR STANDALONE TOOLS ===")
    categories_to_flatten = [
        "Developer & APIs",
        "AI & LLM Tools",
        "Linux, Homelab & Systems",
        "Media, Audio & Design",
        "Productivity & AI Tools",
        "Education",
        "Events & Hackathons",
        "Blueprints & Architecture"
    ]

    for cat_name in categories_to_flatten:
        items = VaultResource.objects.filter(category__icontains=cat_name[:8])
        for item in items:
            item.subcategory = ""
            item.save()

    print("\n=== 5. RESULTING DYNAMIC VAULT HIERARCHY ===")
    from growth.views import get_categories_with_metadata
    cats = get_categories_with_metadata()
    print(f"Total Resources: {VaultResource.objects.count()}")
    print(f"Total Categories: {len(cats)}")
    for c in cats:
        sub_info = [f"{s['name']} ({s['count']})" for s in c.get('subcategories', [])]
        print(f" {c.get('icon', '📁')} {c['name']} (Total: {c['count']}) -> Subcategories: {sub_info}")

if __name__ == "__main__":
    migrate()
