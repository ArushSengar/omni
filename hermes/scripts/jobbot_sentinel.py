#!/usr/bin/env python3
"""
jobbot_sentinel.py — Autonomous CLI JobBot & Career Sentinel for Arush Sengar.
Can be executed standalone, via cron, or invoked by omni_growth_sentinel.py.
Scans for high-accuracy remote cybersecurity / devsecops roles and updates Omni Hub.
"""

import os
import sys
from pathlib import Path

# Add paths
sys.path.insert(0, "/home/arush")
sys.path.insert(0, "/home/arush/omni_hub")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "omni_hub"))

# Initialize Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "omni_hub.settings")
try:
    import django
    django.setup()
except Exception as e:
    pass

try:
    from growth import jobbot_engine
except ImportError:
    import jobbot_engine


def run_career_sentinel(min_score: int = 65, sync_vault: bool = True) -> dict:
    """Run full automated career scan and database sync."""
    print("=" * 65)
    print("   🎯 OMNI CAREER SENTINEL & AUTONOMOUS JOBBOT DISCOVERY   ")
    print("=" * 65)
    result = jobbot_engine.scan_and_sync_jobs(min_score=min_score, sync_vault=sync_vault)
    print("=" * 65)
    return result


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Omni Career Sentinel & JobBot")
    parser.add_argument("--min-score", type=int, default=65, help="Minimum match score threshold")
    parser.add_argument("--no-vault", action="store_true", help="Do not cross-index into OmniVault")
    args = parser.parse_args()

    run_career_sentinel(min_score=args.min_score, sync_vault=not args.no_vault)

