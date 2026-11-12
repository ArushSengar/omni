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

def recluster():
    print("=== RE-CLUSTERING VAULT INTO 8 BROAD DOMAINS WITH DYNAMIC TAGS ===")
    
    # 1. Claude & Agent Skills
    for r in VaultResource.objects.filter(category__icontains="Claude"):
        r.category = "Claude & Agent Skills"
        r.subcategory = ""
        r.save()

    # 2. Developer & System Tools (Merge Dev & APIs + Linux Homelab)
    for r in VaultResource.objects.filter(category__in=["Developer & APIs", "Linux, Homelab & Systems"]):
        r.category = "Developer & System Tools"
        r.subcategory = ""
        r.save()

    # 3. AI & Machine Intelligence (Merge AI & LLM Tools + Productivity & AI Tools)
    for r in VaultResource.objects.filter(category__in=["AI & LLM Tools", "Productivity & AI Tools"]):
        r.category = "AI & Machine Intelligence"
        r.subcategory = ""
        r.save()

    # 4. Media, Creative & Design
    for r in VaultResource.objects.filter(category__icontains="Media"):
        r.category = "Media, Creative & Design"
        r.subcategory = ""
        r.save()

    # 5. Education & Roadmaps (Merge Education + Events & Hackathons)
    for r in VaultResource.objects.filter(category__in=["Education", "Events & Hackathons"]):
        r.category = "Education & Roadmaps"
        r.subcategory = ""
        r.save()

    # 6. Blueprints & Architecture
    for r in VaultResource.objects.filter(category__icontains="Blueprint"):
        r.category = "Blueprints & Architecture"
        r.subcategory = "System Specs"
        r.save()

    # 7. Cyber Security & Pentesting
    for r in VaultResource.objects.filter(category__icontains="Cyber Security"):
        r.category = "Cyber Security & Pentesting"
        t = (r.title or "").lower()
        s = (r.subcategory or "").lower()
        if any(k in t or k in s for k in ["autopsy", "forensic", "volatility", "ftk", "steghide", "server forensics", "memory forensics"]):
            r.subcategory = "Forensics & Analysis"
        elif any(k in t or k in s for k in ["tryhackme", "hackthebox", "blue team labs"]):
            r.subcategory = "Labs & Training"
        elif any(k in t or k in s for k in ["osint", "fingerprint", "behindthemail"]):
            r.subcategory = "OSINT & Recon"
        else:
            r.subcategory = "Security Tools & Exploits"
        r.save()

    # 8. Career & Opportunities
    for r in VaultResource.objects.filter(category__icontains="Career"):
        r.category = "Career & Opportunities"
        t = (r.title or "").lower()
        s = (r.subcategory or "").lower()
        if any(k in t or k in s for k in ["hiring contest", "roadmap", "internship roadmap"]):
            r.subcategory = "Roadmaps & Contests"
        elif any(k in t or k in s for k in ["cybersecurity", "security telemetry", "pentest", "web3 business", "tier iii"]):
            r.subcategory = "Cybersecurity"
        elif any(k in t or k in s for k in ["devsecops", "cloud", "solutions engineer", "full-stack"]):
            r.subcategory = "DevSecOps & Cloud"
        elif any(k in t or k in s for k in ["soc", "threat", "content reviewer", "support specialist", "solutions architect", "frontend"]):
            r.subcategory = "SOC & Threat Monitoring"
        else:
            r.subcategory = "Python & Backend Systems"
        r.save()

    print("\n=== FINAL RE-CLUSTERED CATEGORIES ===")
    from growth.views import get_categories_with_metadata
    cats = get_categories_with_metadata()
    print(f"Total Resources: {VaultResource.objects.count()}")
    print(f"Total Broad Categories: {len(cats)}")
    for c in cats:
        sub_info = [f"{s['name']} ({s['count']})" for s in c.get('subcategories', [])]
        print(f" {c.get('icon', '📁')} {c['name']} (Total: {c['count']}) -> Subcategories: {sub_info}")

if __name__ == "__main__":
    recluster()

