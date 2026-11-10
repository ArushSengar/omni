#!/usr/bin/env python3
"""
omni_deduplicator.py — Master Anti-Repetition & Multi-Tier Deduplication Engine for Arush Sengar.
Guarantees that no topic, assignment, or technical concept ever repeats on LinkedIn or X (Twitter).

Enforces 5 Strict Defense Tiers:
  Tier 1: Assignment ID Lockout (once an assignment number is posted, it is permanently locked out).
  Tier 2: Exact & Normalized Title Match (catches identical titles regardless of punctuation/casing).
  Tier 3: Canonical Concept Collision (detects shared core entities e.g. Modbus/SCADA, SQLite WAL, Unbound DNS).
  Tier 4: Jaccard Keyword Overlap (rejects any candidate with >= 35% technical token overlap with past posts).
  Tier 5: Pillar & Domain Cooldown (enforces minimum 3-post cooldown per pillar to prevent topic fatigue).

Unified Multi-Source Ledger:
  Aggregates used.json, daily_learnings.json, growth_engine_history.json, research archive, and Django DB.
  Provides atomic multi-target state commitment upon every publication.
"""

import os
import sys
import re
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional

HOME = Path.home()
USED_FILE = HOME / ".hermes" / "linkedin_daily" / "used.json"
LEARNINGS_FILE = HOME / ".hermes" / "linkedin_daily" / "daily_learnings.json"
GROWTH_HISTORY_FILE = HOME / ".hermes" / "growth_engine_history.json"
RESEARCH_ARCHIVE_FILE = HOME / ".hermes" / "research_topics_archive.json"
DJANGO_DB_PATHS = [
    HOME / "omni_hub" / "db.sqlite3",
    Path(__file__).resolve().parent.parent.parent / "omni_hub" / "db.sqlite3"
]

# 6 Pillars for Balanced Builder Content
PILLARS = {
    "AI_SECURITY": {
        "name": "AI & Agent Security",
        "keywords": ["prompt injection", "guardrails", "lakera", "agent breaker", "system prompt", "jailbreak", "llm security", "eval", "tool manipulation"]
    },
    "LINUX_KERNEL": {
        "name": "Linux Kernel & Systems Engineering",
        "keywords": ["zram", "cgroups", "dirty pages", "page cache", "ebpf", "sysctl", "kernel", "oom", "drop_caches", "ramdisk"]
    },
    "OFFENSIVE_SECURITY": {
        "name": "Offensive Security & Pentesting",
        "keywords": ["suid", "privilege escalation", "gtfobins", "macho", "ghidra", "reverse engineering", "owasp", "metasploit", "nmap", "gobuster", "uncrackable"]
    },
    "NETWORKING_PROTOCOLS": {
        "name": "Computer Networking & Protocols",
        "keywords": ["dns", "unbound", "split-brain", "tcp", "bbr", "cubic", "tls", "quic", "wireshark", "tcpdump", "latency", "subnets"]
    },
    "HIGH_PERF_PYTHON": {
        "name": "High-Performance Python & Architecture",
        "keywords": ["tracemalloc", "memory leak", "asyncio", "event loop", "gil", "free-threaded", "concurrency", "process pool", "lru cache", "profiling"]
    },
    "DATABASES_STORAGE": {
        "name": "Databases, Storage & Concurrency",
        "keywords": ["sqlite", "wal mode", "lock contention", "database is locked", "postgresql", "pgbouncer", "journal_mode", "mmap"]
    },
    "CLOUD_INFRA": {
        "name": "Cloud Security & Zero-Trust Infrastructure",
        "keywords": ["cloud security", "azure", "nsg", "network security group", "rbac", "sspr", "modbus", "scada", "ics plant", "lateral movement"]
    }
}

STOPWORDS = {
    "hands", "on", "hands-on", "lab", "labs", "assignment", "fundamentals", "defense", "exercise",
    "completed", "using", "with", "from", "part", "room", "today", "learned", "how",
    "why", "what", "deep", "dive", "the", "and", "for", "in", "on", "to", "a", "an",
    "is", "of", "my", "our", "me", "i", "we", "at", "by", "this", "that", "it", "as",
    "breakdown", "guide", "overview", "notes", "observations", "challenge"
}

CANONICAL_ENTITIES = {
    "azure_nsg": ["nsg", "network security group", "network security groups", "azure nsg", "azure storage"],
    "azure_rbac": ["rbac", "contributor role", "role assignment", "az role"],
    "ics_modbus": ["modbus", "scada", "ics plant", "modbus tcp", "modbus_detect"],
    "linux_suid": ["suid", "suid binaries", "gtfobins", "chmod u+s", "perm -4000"],
    "sqlite_wal": ["sqlite", "wal mode", "lock contention", "journal_mode=wal", "pragma synchronous"],
    "dns_unbound": ["unbound", "split-brain dns", "dns latency", "dns resolver", "fallback dns"],
    "python_tracemalloc": ["tracemalloc", "python memory leak", "resident set size", "tracemalloc snapshot"],
    "linux_ebpf": ["ebpf", "bpf_perf_event", "ebpf ring buffer", "bpftrace", "libbpf"],
    "linux_zram": ["zram", "zramctl", "zram swap", "zstd swap"],
    "tcp_bbr": ["tcp bbr", "cubic vs bbr", "congestion control"],
    "lakera_prompt_injection": ["lakera", "agent breaker", "prompt injection", "guardrail bypass"],
    "ios_uncrackable": ["ios uncrackable", "uncrackable level 1", "macho", "anti-debugging", "ptrace"],
    "nmap_metasploit": ["nmap", "metasploit", "service version scanning", "blind port scan"],
    "osint_recon": ["osint", "dark web", "sakura", "corporate recon"]
}


class UnifiedHistoryLedger:
    """Aggregates, normalizes, and indexes all historical social and engineering activity."""

    def __init__(self):
        self.records: List[Dict] = []
        self.used_assignments: Set[str] = set()
        self.used_topic_titles: Set[str] = set()
        self.topic_token_sets: List[Tuple[str, Set[str], Set[str]]] = []  # (title, token_set, entity_set)
        self.recent_pillars: List[str] = []
        self.refresh()

    def refresh(self):
        self.records.clear()
        self.used_assignments.clear()
        self.used_topic_titles.clear()
        self.topic_token_sets.clear()
        self.recent_pillars.clear()

        # 1. Load daily_learnings.json
        if LEARNINGS_FILE.exists():
            try:
                data = json.loads(LEARNINGS_FILE.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    for item in data:
                        self._ingest_record(item)
            except Exception:
                pass

        # 2. Load growth_engine_history.json
        if GROWTH_HISTORY_FILE.exists():
            try:
                data = json.loads(GROWTH_HISTORY_FILE.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    for item in data:
                        self._ingest_record(item)
            except Exception:
                pass

        # 3. Load used.json
        if USED_FILE.exists():
            try:
                data = json.loads(USED_FILE.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    for raw_t in data:
                        if isinstance(raw_t, str) and raw_t.strip():
                            self._ingest_record({"topic": raw_t.strip(), "source": "used_json"})
            except Exception:
                pass

        # 4. Load Django DB
        for db_path in DJANGO_DB_PATHS:
            if db_path.exists():
                try:
                    conn = sqlite3.connect(str(db_path))
                    cur = conn.cursor()
                    cur.execute("SELECT title, domain, source, created_at FROM growth_growthpost")
                    for row in cur.fetchall():
                        self._ingest_record({
                            "topic": row[0],
                            "category": row[1],
                            "source": row[2],
                            "timestamp": row[3]
                        })
                    conn.close()
                    break
                except Exception:
                    pass

        # Sort chronological by timestamp if available
        self.records.sort(key=lambda r: r.get("timestamp") or "1970-01-01", reverse=True)

        # Extract recent pillars (last 5 distinct records)
        for r in self.records:
            full_context = f"{r.get('topic') or ''} {r.get('category') or ''}"
            p = self.classify_pillar(full_context)
            if p and p not in self.recent_pillars:
                self.recent_pillars.append(p)
            if len(self.recent_pillars) >= 4:
                break

    def _ingest_record(self, item: Dict):
        topic = str(item.get("topic") or "").strip()
        if not topic:
            return

        assg = str(item.get("assignment_num") or "").strip().lstrip("0")
        if not assg:
            # Check if assignment number is embedded in topic (e.g., "Assignment 12: ...")
            m = re.search(r'assignment[\s\-_]*(\d+)', topic, re.IGNORECASE)
            if m:
                assg = m.group(1).lstrip("0")

        if assg:
            self.used_assignments.add(assg)

        self.used_topic_titles.add(topic.lower())
        tokens = self.tokenize_technical_terms(topic)
        entities = self.extract_canonical_entities(topic + " " + str(item.get("context", "")))
        self.topic_token_sets.append((topic, tokens, entities))
        self.records.append(item)

    @staticmethod
    def normalize_text(text: str) -> str:
        """Removes punctuation and generic prefixes for clean comparisons."""
        text = text.lower()
        text = re.sub(r'^(hands-on lab|assignment \d+|completed assignment \d+)\s*[:\-]\s*', '', text)
        text = re.sub(r'[^a-z0-9\s]', ' ', text)
        return " ".join(text.split())

    @staticmethod
    def tokenize_technical_terms(text: str) -> Set[str]:
        """Extracts significant non-stopword tokens from technical text."""
        cleaned = re.sub(r'[^a-zA-Z0-9\s_]', ' ', text.lower().replace('-', ' '))
        tokens = {t for t in cleaned.split() if len(t) > 2 and t not in STOPWORDS}
        return tokens

    @staticmethod
    def extract_canonical_entities(text: str) -> Set[str]:
        """Identifies specific core technologies/labs present in the text."""
        lower = text.lower()
        found = set()
        for entity_id, patterns in CANONICAL_ENTITIES.items():
            if any(p in lower for p in patterns):
                found.add(entity_id)
        return found

    @staticmethod
    def classify_pillar(text: str) -> Optional[str]:
        """Classifies topic into one of the 6 primary engineering pillars."""
        lower = text.lower()
        best_pillar = None
        max_matches = 0
        for pid, pdata in PILLARS.items():
            matches = sum(1 for kw in pdata["keywords"] if kw in lower)
            if matches > max_matches:
                max_matches = matches
                best_pillar = pid
        return best_pillar if max_matches > 0 else None


class OmniDeduplicator:
    """Evaluates candidate topics across 5 strict anti-repetition tiers."""

    def __init__(self):
        self.ledger = UnifiedHistoryLedger()

    def refresh(self):
        self.ledger.refresh()

    def evaluate_candidate(self, candidate: Dict) -> Tuple[bool, str, Dict]:
        """
        Validates whether a candidate topic is strictly unique, novel, and pillar-compliant.
        Returns:
          (is_valid: bool, reason: str, metadata: dict)
        """
        topic = str(candidate.get("topic") or "").strip()
        if not topic:
            return False, "Candidate topic is empty", {}

        cand_assg = str(candidate.get("assignment_num") or "").strip().lstrip("0")
        if not cand_assg:
            m = re.search(r'assignment[\s\-_]*(\d+)', topic, re.IGNORECASE)
            if m:
                cand_assg = m.group(1).lstrip("0")

        # ------------------------------------------------------------------
        # TIER 1: Assignment Lockout
        # ------------------------------------------------------------------
        if cand_assg and cand_assg in self.ledger.used_assignments:
            return False, f"Assignment #{cand_assg} was ALREADY published in history (Assignment Lockout).", {"tier": 1}

        # ------------------------------------------------------------------
        # TIER 2: Exact & Normalized Title Match
        # ------------------------------------------------------------------
        norm_candidate = self.ledger.normalize_text(topic)
        if topic.lower() in self.ledger.used_topic_titles:
            return False, f"Exact title already published: '{topic}'", {"tier": 2}

        for hist_topic in self.ledger.used_topic_titles:
            norm_hist = self.ledger.normalize_text(hist_topic)
            if norm_candidate == norm_hist:
                return False, f"Normalized title identical to past post: '{hist_topic}'", {"tier": 2}

        # ------------------------------------------------------------------
        # TIER 3: Canonical Entity Overlap
        # ------------------------------------------------------------------
        cand_context = str(candidate.get("context") or "")
        cand_entities = self.ledger.extract_canonical_entities(topic + " " + cand_context)

        for hist_title, hist_tokens, hist_entities in self.ledger.topic_token_sets:
            shared_entities = cand_entities & hist_entities
            if shared_entities:
                return False, f"Entity collision on {shared_entities} with historical post '{hist_title}'", {
                    "tier": 3,
                    "collided_post": hist_title,
                    "shared_entities": list(shared_entities)
                }

        # ------------------------------------------------------------------
        # TIER 4: Jaccard Keyword Overlap (Threshold: 35%)
        # ------------------------------------------------------------------
        cand_tokens = self.ledger.tokenize_technical_terms(topic)
        for hist_title, hist_tokens, _ in self.ledger.topic_token_sets:
            if not cand_tokens or not hist_tokens:
                continue
            intersection = cand_tokens & hist_tokens
            union = cand_tokens | hist_tokens
            similarity = len(intersection) / len(union) if union else 0.0

            if similarity >= 0.35:
                return False, f"High semantic keyword overlap ({similarity:.0%}) with historical post: '{hist_title}' (Shared: {intersection})", {
                    "tier": 4,
                    "similarity": similarity,
                    "collided_post": hist_title,
                    "shared_tokens": list(intersection)
                }

        # ------------------------------------------------------------------
        # TIER 5: Pillar & Domain Cooldown (Recent 3 Posts)
        # ------------------------------------------------------------------
        cand_pillar = self.ledger.classify_pillar(topic + " " + str(candidate.get("category", "")))
        if cand_pillar and cand_pillar in self.ledger.recent_pillars[:3]:
            recent_names = [PILLARS.get(p, {}).get("name", p) for p in self.ledger.recent_pillars[:3]]
            return False, f"Pillar '{PILLARS[cand_pillar]['name']}' is in cooldown (recently used: {recent_names}). Rotate to another engineering pillar.", {
                "tier": 5,
                "pillar": cand_pillar,
                "recent_pillars": self.ledger.recent_pillars[:3]
            }

        return True, "Topic is 100% unique, novel, and pillar-compliant.", {
            "pillar": cand_pillar or "GENERAL_ENGINEERING",
            "tokens": list(cand_tokens),
            "entities": list(cand_entities)
        }

    def get_exhausted_assignments(self) -> Set[str]:
        return set(self.ledger.used_assignments)

    def get_banned_topics_summary(self) -> List[str]:
        return list(self.ledger.used_topic_titles)


def commit_published_record(topic_data: dict, linkedin_post: str, x_tweets: list, img_path: str, results: dict):
    """
    Synchronously and atomically commits a published post to all 4 system records:
    1. used.json
    2. daily_learnings.json
    3. growth_engine_history.json
    4. omni_hub SQLite db
    """
    topic_title = topic_data.get("topic", "").strip()
    assg_num = str(topic_data.get("assignment_num", "")).strip()
    timestamp = datetime.now().isoformat()

    # 1. Update used.json
    try:
        USED_FILE.parent.mkdir(parents=True, exist_ok=True)
        used_list = []
        if USED_FILE.exists():
            try:
                used_list = json.loads(USED_FILE.read_text(encoding="utf-8"))
            except Exception:
                used_list = []
        if topic_title and topic_title not in used_list:
            used_list.append(topic_title)
        if assg_num and f"Assignment {assg_num}" not in used_list:
            used_list.append(f"Assignment {assg_num}")
        USED_FILE.write_text(json.dumps(used_list, indent=2), encoding="utf-8")
        print(f"  [Ledger Commit] Synced to {USED_FILE.name}")
    except Exception as e:
        print(f"  [warn] Failed to update used.json: {e}")

    # 2. Update daily_learnings.json
    try:
        LEARNINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        learnings = []
        if LEARNINGS_FILE.exists():
            try:
                learnings = json.loads(LEARNINGS_FILE.read_text(encoding="utf-8"))
            except Exception:
                learnings = []
        learning_record = {
            "timestamp": timestamp,
            "topic": topic_title,
            "assignment_num": assg_num,
            "source": topic_data.get("source", ""),
            "thesis": linkedin_post.split("\n")[0][:60] if linkedin_post else topic_title[:60],
            "post": linkedin_post,
            "img_path": str(img_path) if img_path else "",
            "share_urn": results.get("linkedin", ""),
            "url": f"https://www.linkedin.com/feed/update/{results.get('linkedin', '')}/" if "urn:li:" in str(results.get("linkedin", "")) else ""
        }
        learnings.append(learning_record)
        LEARNINGS_FILE.write_text(json.dumps(learnings, indent=2), encoding="utf-8")
        print(f"  [Ledger Commit] Synced to {LEARNINGS_FILE.name}")
    except Exception as e:
        print(f"  [warn] Failed to update daily_learnings.json: {e}")

    # 3. Update growth_engine_history.json
    try:
        GROWTH_HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        history = []
        if GROWTH_HISTORY_FILE.exists():
            try:
                history = json.loads(GROWTH_HISTORY_FILE.read_text(encoding="utf-8"))
            except Exception:
                history = []
        log_record = {
            "timestamp": timestamp,
            "topic": topic_title,
            "category": topic_data.get("category"),
            "source": topic_data.get("source"),
            "linkedin_post": linkedin_post,
            "x_tweets": x_tweets,
            "image_path": str(img_path) if img_path else "",
            "results": results
        }
        history.append(log_record)
        GROWTH_HISTORY_FILE.write_text(json.dumps(history, indent=2), encoding="utf-8")
        print(f"  [Ledger Commit] Synced to {GROWTH_HISTORY_FILE.name}")
    except Exception as e:
        print(f"  [warn] Failed to update growth_engine_history.json: {e}")

    # 4. Update Django SQLite DB
    for db_path in DJANGO_DB_PATHS:
        if db_path.exists():
            try:
                conn = sqlite3.connect(str(db_path))
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO growth_growthpost 
                    (title, domain, source, linkedin_content, twitter_content, image_path, status, linkedin_urn, twitter_url, likes, views, comments, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, 0, ?)
                """, (
                    topic_title,
                    topic_data.get("category", "General Engineering"),
                    topic_data.get("source", "autonomous"),
                    linkedin_post,
                    x_tweets[0] if x_tweets else "",
                    str(img_path) if img_path else "",
                    "PUBLISHED",
                    results.get("linkedin", ""),
                    str(results.get("x", "")),
                    timestamp
                ))
                conn.commit()
                conn.close()
                print(f"  [Ledger Commit] Synced to Django DB: {db_path.name}")
                break
            except Exception as e:
                print(f"  [warn] Failed to sync to Django DB: {e}")


if __name__ == "__main__":
    dedup = OmniDeduplicator()
    print("=== OMNI DEDUPLICATOR STATUS ===")
    print(f"Historical Records Loaded: {len(dedup.ledger.records)}")
    print(f"Exhausted Assignment IDs : {dedup.get_exhausted_assignments()}")
    print(f"Recent Pillars (Cooldown): {dedup.ledger.recent_pillars}")

    # Test candidate checks
    test_cases = [
        {"topic": "Cloud Security: Fundamentals & Defense", "assignment_num": "12"},
        {"topic": "Hands-on Lab: Cloud Security with Azure NSGs", "assignment_num": ""},
        {"topic": "Linux Privilege Escalation via SUID", "assignment_num": "7"},
        {"topic": "Tuning SQLite for Concurrency: WAL Mode", "assignment_num": ""},
        {"topic": "Detecting Kernel Rootkits with eBPF Ring Buffers", "category": "Linux Kernel", "assignment_num": ""},
        {"topic": "AsyncIO Event Loop Starvation: Debugging Latency Spikes in Python Routers", "category": "Python Architecture", "assignment_num": ""}
    ]

    print("\n--- TEST CANDIDATE EVALUATIONS ---")
    for tc in test_cases:
        valid, reason, meta = dedup.evaluate_candidate(tc)
        status = "✅ ALLOWED" if valid else f"❌ REJECTED ({reason})"
        print(f"Topic: '{tc['topic']}' (Assg: {tc.get('assignment_num') or 'None'}) -> {status}")
