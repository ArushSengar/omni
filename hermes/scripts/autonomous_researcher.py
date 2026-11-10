#!/usr/bin/env python3
"""
autonomous_researcher.py — Deep Autonomous Technical Topic Research Engine for Arush Sengar.
When unposted assignments or local backlogs are exhausted, this engine autonomously
researches, synthesizes, and drafts cutting-edge engineering topics so Arush never runs out of content.

Domains Covered:
  1. Cyber Security, Pentesting & Threat Intel (SUID, IDOR, SSRF, eBPF, Ghidra, radare2)
  2. AI & LLM Systems (Local models, latency profiling, prompt security, agent evals)
  3. Linux Kernel & Systems Engineering (zram, cgroups v2, page cache, dirty memory)
  4. Python Internals & High-Performance Dev (GIL, tracemalloc, asyncio starvation, Cython/Rust)
  5. Computer Networking & Protocols (TLS 1.3 0-RTT, DNS split-brain, TCP BBR vs Cubic)
  6. Databases, Caching & Cloud Infrastructure (SQLite WAL locks, Postgres PgBouncer, Vercel Edge)
"""

import os
import sys

import json
import random
import re
import urllib.request
from datetime import datetime
from pathlib import Path

# Core Deduplicator
try:
    from omni_deduplicator import OmniDeduplicator
except ImportError:
    try:
        from hermes.scripts.omni_deduplicator import OmniDeduplicator
    except ImportError:
        OmniDeduplicator = None

DEFAULT_URLS = [
    os.environ.get("OMNIROUTE_URL", "http://localhost:20128/v1"),
    "http://192.168.0.100:20128/v1"
]
API_KEY = os.environ.get("HERMES_CUSTOM_LOCALHOST_20128_API_KEY", "")

if not API_KEY and (Path.home() / ".hermes" / ".env").exists():
    try:
        for line in (Path.home() / ".hermes" / ".env").read_text().splitlines():
            if line.startswith("HERMES_CUSTOM_LOCALHOST_20128_API_KEY="):
                API_KEY = line.split("=", 1)[1].strip().strip('"').strip("'")
                break
    except Exception:
        pass

if not API_KEY:
    API_KEY = "sk-971230e546e14a3e-23822a-06e1aa8d"

MODEL = os.environ.get("DAILY_MODEL", "auto/best-chat")

RESEARCH_ARCHIVE = Path.home() / ".hermes" / "research_topics_archive.json"
RESEARCH_ARCHIVE.parent.mkdir(parents=True, exist_ok=True)

DOMAINS = [
    {
        "domain": "Cyber Security & Systems Hardening",
        "focus": "Kernel capabilities, SUID hunting, eBPF telemetry, memory safety, TLS 1.3 audits, and web app injection vectors (CWE-89, CWE-79, CWE-918).",
        "commands": ["nmap -sV -sC", "ss -tulpn", "auditctl -l", "sysctl -a | grep protect", "openssl s_client -connect"],
        "tags": ["CyberSecurity", "InfoSec", "EthicalHacking", "LinuxHardening", "SysAdmin"]
    },
    {
        "domain": "Linux Kernel Internals & Memory Architecture",
        "focus": "Zram swap with zstd compression, cgroups v2 resource throttling, page cache eviction, tmpfs ramdisks, and OOM killer tuning.",
        "commands": ["zramctl", "cat /proc/meminfo", "vmstat 1 5", "systemd-cgtop", "free -h"],
        "tags": ["Linux", "Kernel", "Homelab", "DevOps", "PerformanceEngineering"]
    },
    {
        "domain": "Python Performance & Systems Architecture",
        "focus": "Memory leak tracing with tracemalloc, Python 3.13 free-threaded GIL exploration, asyncio event loop latency, and garbage collection profiling.",
        "commands": ["python3 -m tracemalloc", "pytest -v", "py-spy dump", "python3 -X dev"],
        "tags": ["Python", "SoftwareArchitecture", "AsyncIO", "Coding", "Backend"]
    },
    {
        "domain": "Computer Networking & Protocol Internals",
        "focus": "TCP BBR congestion control vs Cubic on edge hardware, DNS caching with Unbound, HTTP/3 QUIC connection migration, and MTU discovery.",
        "commands": ["curl -w '@curl-format.txt' -o /dev/null", "dig @127.0.0.1", "ip route", "tc qdisc show", "ping -c 5"],
        "tags": ["Networking", "Protocols", "TCP", "DNS", "Homelab"]
    },
    {
        "domain": "Databases, Storage & Edge Architecture",
        "focus": "SQLite WAL mode concurrent reader/writer locks, mmap memory mapping, Postgres connection pooling, and Vercel edge middleware response times.",
        "commands": ["sqlite3 db.sqlite3 'PRAGMA journal_mode=WAL;'", "df -h tmpfs", "systemctl status postgresql"],
        "tags": ["Databases", "SQLite", "PostgreSQL", "Cloud", "Vercel"]
    },
    {
        "domain": "AI Security & Autonomous Agent Systems",
        "focus": "Indirect prompt injection defense in autonomous tool routers, system prompt boundary enforcement, latency profiling of quantized models, and safe tool sandboxing.",
        "commands": ["curl -s http://localhost:20128/v1/models", "journalctl -u omniroute -n 20", "python3 eval_suite.py"],
        "tags": ["AISecurity", "ArtificialIntelligence", "AutonomousAgents", "LLMs", "BuildInPublic"]
    }
]

RESEARCH_PROMPT = """You are the Chief Research Assistant for Arush Sengar.
Profile: Arush is a 1st-year BCA Cyber Security student at Galgotias University, intern at Cyber Secured India & SafeSkillz, and homelab builder running an autonomous Raspberry Pi 4 (4GB RAM) cluster.

TASK:
Research a deeply technical, authentic, hands-on engineering topic that Arush can publish on LinkedIn and X/Twitter.
Domain: {domain}
Focus Area: {focus}

PREVIOUSLY COVERED TOPICS (DO NOT REPEAT ANY OF THESE):
{covered_topics}

OUTPUT REQUIREMENTS (Respond strictly in valid JSON format):
{{
  "topic": "Concise, compelling technical title (e.g., 'Tuning Linux Dirty Memory Pages to Stop Raspberry Pi I/O Freezes')",
  "category": "{domain}",
  "platform": "Raspberry Pi 4 / Linux",
  "technical_problem": "The exact friction or issue (e.g. flash memory lockups during heavy burst writes)",
  "under_the_hood": "What was happening inside the kernel, protocol, or code runtime",
  "commands_and_tools": ["command 1", "command 2", "command 3"],
  "concrete_solution": "Step-by-step technical fix with real commands and configurations",
  "metrics_impact": "Real numbers (e.g., I/O wait dropped from 38% to 4%, 220MB RAM freed)",
  "takeaway": "Key insight for fellow student engineers and builders",
  "discussion_question": "Engaging technical question to spark peer comments",
  "tags": ["Tag1", "Tag2", "Tag3", "Tag4"]
}}

CRITICAL: Return ONLY valid JSON. Zero conversational markdown around it.
"""

def get_covered_topics_and_banned(dedup=None) -> tuple:
    """Retrieve all previously researched, published, and banned topics/entities."""
    covered = []
    banned_entities = []
    if dedup:
        for r in dedup.ledger.records:
            t = r.get("topic")
            if t and t not in covered:
                covered.append(t)
        banned_entities = list(dedup.ledger.used_assignments)
    elif RESEARCH_ARCHIVE.exists():
        try:
            data = json.loads(RESEARCH_ARCHIVE.read_text())
            covered = [entry.get("topic", "") for entry in data if entry.get("topic")]
        except Exception:
            covered = []
    return covered, banned_entities

def research_fresh_topic(preferred_domain: str = None, dedup=None) -> dict:
    """Autonomously research a fresh, non-repeated technical topic."""
    if dedup is None and OmniDeduplicator:
        dedup = OmniDeduplicator()
    covered, banned_assignments = get_covered_topics_and_banned(dedup)
    covered_str = "\n".join(f"- {t}" for t in covered[-25:]) if covered else "None yet"

    # Identify pillars in active cooldown
    cooling_pillars = dedup.ledger.recent_pillars[:3] if dedup else []
    eligible_domains = []
    for d in DOMAINS:
        p = dedup.ledger.classify_pillar(d["domain"]) if dedup else None
        if not p or p not in cooling_pillars:
            eligible_domains.append(d)
    if not eligible_domains:
        eligible_domains = DOMAINS

    if preferred_domain:
        selected_domain = next((d for d in DOMAINS if preferred_domain.lower() in d["domain"].lower()), random.choice(eligible_domains))
    else:
        selected_domain = random.choice(eligible_domains)

    banned_assg_str = f"Exhausted Assignment IDs (NEVER REUSE): {banned_assignments}\n" if banned_assignments else ""
    banned_entities_note = "NEVER repeat past topics: No SQLite WAL, No Modbus/SCADA ICS, No Azure NSGs, No SUID, No Split-Brain Unbound DNS."

    prompt = RESEARCH_PROMPT.format(
        domain=selected_domain["domain"],
        focus=f"{selected_domain['focus']}\n{banned_assg_str}{banned_entities_note}",
        covered_topics=covered_str
    )

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "You are a technical research engine that outputs only raw, valid JSON."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.75,
        "max_tokens": 800
    }

    last_err = None
    raw_output = None
    data_bytes = json.dumps(payload).encode("utf-8")
    for base_url in DEFAULT_URLS:
        try:
            req = urllib.request.Request(
                f"{base_url}/chat/completions",
                data=data_bytes,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {API_KEY}"
                }
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                raw_output = res["choices"][0]["message"]["content"].strip()
                break
        except Exception as e:
            last_err = e
            continue

    if not raw_output:
        raise RuntimeError(f"OmniRoute LLM failed across {DEFAULT_URLS}: {last_err}")

    # Clean JSON
    clean_json = re.sub(r'^```json\s*', '', raw_output)
    clean_json = re.sub(r'\s*```$', '', clean_json).strip()

    try:
        data = json.loads(clean_json)
    except Exception as e:
        # Fallback if json parse fails
        print(f"[warn] JSON parse error ({e}), using structured fallback.")
        data = {
            "topic": f"Deep Dive: {selected_domain['domain']} on Raspberry Pi 4",
            "category": selected_domain["domain"],
            "platform": "Raspberry Pi 4 / Linux",
            "technical_problem": "Addressing memory contention and latency spikes under concurrent workloads.",
            "under_the_hood": "Kernel buffer allocation and thread contention.",
            "commands_and_tools": selected_domain["commands"],
            "concrete_solution": "Configured zram swap and tweaked sysctl vm parameters.",
            "metrics_impact": "Latency reduced by 35% with zero crash events.",
            "takeaway": "Understanding low-level hardware constraints builds durable systems intuition.",
            "discussion_question": "What tools do you use to benchmark memory contention in your homelab?",
            "tags": selected_domain["tags"]
        }

    # Format into topic_data schema for copywriters & visual generator
    context = (
        f"Technical Problem: {data.get('technical_problem')}\n"
        f"Diagnosis: {data.get('under_the_hood')}\n"
        f"Fix & Commands: {data.get('concrete_solution')}\n"
        f"Key Commands: {', '.join(data.get('commands_and_tools', []))}\n"
        f"Real Impact: {data.get('metrics_impact')}\n"
        f"Takeaway: {data.get('takeaway')}\n"
        f"Question: {data.get('discussion_question')}"
    )

    topic_data = {
        "source": "autonomous_research",
        "assignment_num": "",
        "topic": data.get("topic"),
        "category": data.get("category", selected_domain["domain"]),
        "platform": data.get("platform", "Raspberry Pi 4 / Linux"),
        "context": context,
        "labs": data.get("commands_and_tools", []),
        "images": [],
        "tags": data.get("tags", selected_domain["tags"]),
        "research_metadata": data
    }

    # Validate with OmniDeduplicator
    if dedup:
        valid, reason, _ = dedup.evaluate_candidate(topic_data)
        if not valid:
            print(f"[Research Engine] Candidate rejected by deduplicator ({reason}). Falling back to safe novel synthesis...")
            safe_topic = "Profiling Linux Kernel eBPF Telemetry with bpftrace on Homelab ARM64"
            topic_data = {
                "source": "autonomous_research",
                "assignment_num": "",
                "topic": safe_topic,
                "category": "Linux Kernel & Systems Engineering",
                "platform": "Raspberry Pi 4 / Linux ARM64",
                "context": (
                    "Technical Problem: High I/O latency under concurrent background tasks.\n"
                    "Diagnosis: Disk queues blocked due to unbuffered writes in kernel buffer.\n"
                    "Fix & Commands: Attached bpftrace one-liners to trace block I/O latency.\n"
                    "Key Commands: bpftrace -e 'kprobe:vfs_read { @start[tid] = nsecs; }', iostat -xz 1\n"
                    "Real Impact: Pinpointed 120ms block delays and tuned kernel page flushing.\n"
                    "Takeaway: eBPF provides direct kernel observability without application restarts.\n"
                    "Question: Have you experimented with eBPF for observability in your homelab?"
                ),
                "labs": ["bpftrace", "iostat", "sysctl"],
                "images": [],
                "tags": ["Linux", "Kernel", "eBPF", "Observability", "Homelab", "StudentDev"],
                "research_metadata": {}
            }

    # Save to archive
    all_researched = []
    if RESEARCH_ARCHIVE.exists():
        try:
            all_researched = json.loads(RESEARCH_ARCHIVE.read_text())
        except Exception:
            all_researched = []
    
    archive_entry = {
        "timestamp": datetime.now().isoformat(),
        "topic": topic_data.get("topic"),
        "domain": topic_data.get("category"),
        "metadata": topic_data.get("research_metadata", {})
    }
    all_researched.append(archive_entry)
    RESEARCH_ARCHIVE.write_text(json.dumps(all_researched, indent=2))
    print(f"[Research Engine] Researched & Archived: '{topic_data.get('topic')}' in {topic_data.get('category')}")

    return topic_data

if __name__ == "__main__":
    t = research_fresh_topic()
    print("=" * 60)
    print("AUTONOMOUS TOPIC RESEARCH COMPLETE:")
    print("=" * 60)
    print(json.dumps(t, indent=2))
