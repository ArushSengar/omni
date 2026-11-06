#!/usr/bin/env python3
"""
linkedin_activity_detector.py — Upgraded Activity & Milestone Detector for Arush.
Scans:
  1. Archived & active assignment DOCX files (/home/arush/assignments_archive/documents/ and /home/arush/)
  2. Pre-extracted assignment media (/home/arush/assignment_media/)
  3. Daily notes (~/posts/notes.md or ~/posts/today_notes.txt)
  4. Curated student backlog (homelab, hackathons, open source projects)
"""

import os
import sys
# Strip stale python3.14 paths
sys.path = [p for p in sys.path if "python3.14" not in p]

import glob
import json
import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime, timedelta

HOME = Path.home()
DOCS_DIR = HOME / "assignments_archive" / "documents"
MEDIA_DIR = HOME / "assignment_media"
NOTES_FILE = HOME / "posts" / "notes.md"
TODAY_NOTES_FILE = HOME / "posts" / "today_notes.txt"
LEARNINGS_FILE = HOME / ".hermes" / "linkedin_daily" / "daily_learnings.json"
USED_FILE = HOME / ".hermes" / "linkedin_daily" / "used.json"

# Curated engineering & student projects backlog when no new docx is due
BACKLOG_TOPICS = [
    {
        "topic": "Running an Autonomous AI Homelab on a 4GB Raspberry Pi 4",
        "category": "Homelab & DevOps",
        "platform": "Raspberry Pi 4",
        "assignment_num": "",
        "labels": ["Systemd Architecture", "OmniRoute AI Gateway", "Resource Watchdog"],
        "context": (
            "Maintained my 24/7 Raspberry Pi 4 home server running OmniRoute AI proxy, systemd units, and local agents. "
            "Faced memory pressure with 4GB RAM under multi-model routing; implemented zram swap, container auto-pruning, "
            "and an automated self-healing watchdog daemon."
        ),
        "tags": ["RaspberryPi", "Homelab", "Linux", "DevOps", "CyberSecurity", "BCA", "StudentDev"]
    },
    {
        "topic": "Debugging Silent Memory Leaks in Python Daemons with tracemalloc",
        "category": "Software Engineering & Python",
        "platform": "Python 3.11 / Linux",
        "assignment_num": "",
        "labels": ["tracemalloc", "Memory Profiling", "Garbage Collection"],
        "context": (
            "Diagnosed a silent memory leak in a long-running background daemon where resident set size grew by 80MB daily. "
            "Standard print debugging failed; used Python's native tracemalloc module to take memory snapshots and identify "
            "unbounded ring buffer allocations. Replaced linear search with an LRU cache."
        ),
        "tags": ["Python", "SoftwareEngineering", "Debugging", "CleanCode", "Performance", "StudentDev"]
    },
    {
        "topic": "Tuning SQLite for Concurrency: Why Enabling WAL Mode Solved Lock Contention",
        "category": "Databases & Storage",
        "platform": "SQLite / Debian Linux",
        "assignment_num": "",
        "labels": ["WAL Mode", "Lock Contention", "Database Optimization"],
        "context": (
            "Encountered 'database is locked' operational errors when concurrent agent processes wrote to a local SQLite ledger. "
            "Instead of installing heavy database servers like PostgreSQL, enabled PRAGMA journal_mode=WAL and PRAGMA synchronous=NORMAL. "
            "Achieved over 4,800 concurrent reads/writes per second with zero lock timeouts."
        ),
        "tags": ["Databases", "SQLite", "Performance", "Backend", "Storage", "DevOps"]
    },
    {
        "topic": "Troubleshooting Split-Brain DNS and Latency Bottlenecks on Local Subnets",
        "category": "Computer Networking",
        "platform": "Networking / Linux",
        "assignment_num": "",
        "labels": ["DNS Resolution", "TCP Handshake", "Wireshark"],
        "context": (
            "Investigated intermittent 2-second API latency spikes across internal homelab services. "
            "Packet analysis with tcpdump and curl format profilers revealed that fallback DNS queries were timing out on non-routable domains. "
            "Configured a local Unbound caching resolver and reduced lookup latency to under 0.8ms."
        ),
        "tags": ["Networking", "DNS", "Sysadmin", "Linux", "Infrastructure", "Protocols"]
    },
    {
        "topic": "SUID Binary Privilege Escalation: How GTFOBins Explains Misconfigurations",
        "category": "Cyber Security & Pentesting",
        "platform": "Linux PrivEsc Lab",
        "assignment_num": "",
        "labels": ["SUID Exploitation", "GTFOBins", "Kernel Permissions"],
        "context": (
            "Completed hands-on Linux privilege escalation exercises targeting misconfigured SUID bits on standard administrative binaries. "
            "Demonstrated how binaries with SUID permissions like base64, find, or vim allow root shell spawning if not properly restricted. "
            "Emphasized principle of least privilege and automated SUID auditing."
        ),
        "tags": ["CyberSecurity", "EthicalHacking", "Linux", "PrivilegeEscalation", "InfoSec", "TryHackMe"]
    },
    {
        "topic": "Hardening Edge Servers with Strict UFW and iptables Egress Policies",
        "category": "Network Security",
        "platform": "UFW / iptables",
        "assignment_num": "",
        "labels": ["Firewall Hardening", "Egress Filtering", "Rate Limiting"],
        "context": (
            "Configured zero-trust perimeter security on a public-facing edge server. "
            "Defaulted to strict incoming deny, rate-limited SSH handshakes to mitigate brute-force attempts, "
            "and restricted outbound traffic strictly to necessary API gateways and DNS resolvers."
        ),
        "tags": ["CyberSecurity", "NetworkSecurity", "Firewall", "DevOps", "Sysadmin", "Linux"]
    },
    {
        "topic": "AsyncIO vs Multiprocessing in Python: Lessons from Writing a High-Throughput Proxy",
        "category": "Software Engineering & Architecture",
        "platform": "Python Architecture",
        "assignment_num": "",
        "labels": ["AsyncIO", "Concurrency", "Event Loops"],
        "context": (
            "Evaluated concurrency models while building a lightweight reverse proxy router. "
            "Discovered that CPU-bound JSON parsing choked the single-threaded asyncio event loop under high load; "
            "solved it by offloading payload decoding to worker process pools while keeping network I/O purely asynchronous."
        ),
        "tags": ["Python", "SoftwareArchitecture", "AsyncIO", "BackendEngineering", "Programming"]
    },
    {
        "topic": "Bulletproof Bash Scripting: Error Traps and Defensive Automation",
        "category": "DevOps & Automation",
        "platform": "Bash / Linux",
        "assignment_num": "",
        "labels": ["Bash Scripting", "Defensive Automation", "Error Traps"],
        "context": (
            "Upgraded mission-critical maintenance shell scripts using defensive scripting principles: "
            "enforced 'set -euo pipefail', atomic file replacements with mktemp, and exit traps to ensure "
            "temporary lockfiles and PID files are always cleaned up even on unexpected termination."
        ),
        "tags": ["DevOps", "Bash", "Linux", "Automation", "Sysadmin", "Scripting"]
    },
    {
        "topic": "Lakera AI Agent Breaker: Bypassing Prompt Injection Guardrails",
        "category": "AI Security",
        "platform": "Lakera AI",
        "assignment_num": "Breaker",
        "labels": ["Indirect Prompt Injection", "Guardrail Analysis", "System Prompt Extraction"],
        "context": (
            "Conducted prompt injection and system prompt extraction assessments on Lakera AI's Agent Breaker platform. "
            "Direct injection was immediately caught; bypassed guardrails using conversational steering and asking the agent to verify logic."
        ),
        "tags": ["AISecurity", "PromptInjection", "Lakera", "EthicalHacking", "InfoSec", "StudentLearning"]
    },
    {
        "topic": "What Being a 1st-Year BCA Student Building in Public Taught Me",
        "category": "Student Builder & Mindset",
        "platform": "Galgotias University",
        "assignment_num": "",
        "labels": ["Building In Public", "Hands-on Learning", "Student Dev"],
        "context": (
            "Reflecting on balancing 1st-year BCA coursework at Galgotias University with autonomous homelab experiments and internships. "
            "Realized that setting up real servers, fixing 3 AM kernel crashes, and breaking code teaches more durable intuition "
            "than reading multiple choice textbooks. Practical experience compound daily."
        ),
        "tags": ["StudentBuilder", "GalgotiasUniversity", "LearningInPublic", "CareerJourney", "ComputerScience"]
    }
]

def extract_docx_metadata(docx_path: str) -> dict:
    """Extracts assignment number, topic, labs, reflection text, and images from a docx."""
    meta = {
        "file": docx_path,
        "filename": Path(docx_path).name,
        "assignment_num": "",
        "topic": "",
        "platform": "TryHackMe",
        "labs": [],
        "reflections": [],
        "images": []
    }
    
    try:
        with zipfile.ZipFile(docx_path, 'r') as z:
            if 'word/document.xml' in z.namelist():
                xml_data = z.read('word/document.xml')
                tree = ET.fromstring(xml_data)
                paras = []
                for p in tree.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p'):
                    txt = "".join([t.text for t in p.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t') if t.text]).strip()
                    if txt:
                        paras.append(txt)
                        
                full_text = "\n".join(paras)
                
                # Regex extraction
                m_assign = re.search(r"Assignment:\s*([0-9]+[a-zA-Z]*)", full_text, re.IGNORECASE)
                if not m_assign:
                    m_assign = re.search(r"Assignment([0-9]+)", Path(docx_path).stem, re.IGNORECASE)
                if m_assign:
                    meta["assignment_num"] = m_assign.group(1).strip()
                    
                m_topic = re.search(r"Topic:\s*([^\n\r]+)", full_text, re.IGNORECASE)
                if m_topic:
                    meta["topic"] = m_topic.group(1).strip()
                    
                m_plat = re.search(r"Platform:\s*([^\n\r]+)", full_text, re.IGNORECASE)
                if m_plat:
                    meta["platform"] = m_plat.group(1).strip()
                    
                # Collect labs & reflections
                for i, p in enumerate(paras):
                    if p.lower().startswith("lab "):
                        meta["labs"].append(p)
                    elif p.lower().startswith("reflection:"):
                        ref_txt = []
                        for j in range(i + 1, min(i + 4, len(paras))):
                            if paras[j].lower().startswith("lab ") or "screenshot" in paras[j].lower():
                                break
                            ref_txt.append(paras[j])
                        meta["reflections"].append(" ".join(ref_txt))
    except Exception as e:
        print(f"Error parsing docx {docx_path}: {e}")
        
    # Check pre-extracted media directory
    stem = Path(docx_path).stem
    candidate_media_dir = MEDIA_DIR / stem
    if candidate_media_dir.exists():
        meta["images"] = sorted(glob.glob(str(candidate_media_dir / "*.*")))
        
    return meta

def get_all_assignments() -> list:
    """Scans all assignment documents in both doc dirs."""
    docs = []
    seen_stems = set()
    
    search_paths = [
        str(DOCS_DIR / "*.docx"),
        str(HOME / "*.docx"),
        str(HOME / "assignments" / "*.docx")
    ]
    
    for pattern in search_paths:
        for p in sorted(glob.glob(pattern)):
            stem = Path(p).stem
            if stem not in seen_stems:
                seen_stems.add(stem)
                meta = extract_docx_metadata(p)
                if meta["topic"]:
                    docs.append(meta)
        # Prioritize assignments with multiple screenshots (2+)
    docs.sort(key=lambda x: len(x.get("images", [])), reverse=True)
    return docs

def get_used_topics() -> list:
    """Reads used topics from used.json and daily_learnings.json."""
    used = set()
    if USED_FILE.exists():
        try:
            for item in json.loads(USED_FILE.read_text()):
                used.add(str(item).strip())
        except Exception:
            pass
    if LEARNINGS_FILE.exists():
        try:
            for entry in json.loads(LEARNINGS_FILE.read_text()):
                if entry.get("topic"):
                    used.add(entry["topic"].strip())
        except Exception:
            pass
    return list(used)

def detect_daily_topic(force_assignment: str = None, force_topic: str = None) -> dict:
    """Selects the best topic for today's post."""
    assignments = get_all_assignments()
    
    # 1. Force by assignment number
    if force_assignment:
        target_str = str(force_assignment).strip().lstrip('0')
        for a in assignments:
            if str(a["assignment_num"]).strip().lstrip('0') == target_str:
                ref_summary = " ".join(a["reflections"]) if a["reflections"] else a["topic"]
                return {
                    "source": "assignment",
                    "assignment_num": a["assignment_num"],
                    "topic": a["topic"],
                    "platform": a["platform"],
                    "context": ref_summary,
                    "labs": a["labs"],
                    "images": a["images"],
                    "tags": ["CyberSecurity", "TryHackMe", "HandsOnLab", "SafeSkillz", "CyberSecuredIndia"]
                }
                
    # 2. Force by custom topic
    if force_topic:
        for b in BACKLOG_TOPICS:
            if b["topic"].lower() in force_topic.lower() or force_topic.lower() in b["topic"].lower():
                return {
                    "source": "backlog",
                    "assignment_num": b.get("assignment_num", ""),
                    "topic": b["topic"],
                    "category": b.get("category", "General Engineering"),
                    "platform": b["platform"],
                    "context": b["context"],
                    "images": [],
                    "tags": b["tags"]
                }
        return {
            "source": "custom",
            "assignment_num": "",
            "topic": force_topic,
            "category": "General Engineering",
            "platform": "CyberSecurity",
            "context": f"Hands-on cybersecurity deep dive: {force_topic}",
            "images": [],
            "tags": ["CyberSecurity", "InfoSec", "EthicalHacking", "StudentDev"]
        }
        
    # 3. Check quick manual notes
    for p in [TODAY_NOTES_FILE, NOTES_FILE]:
        if p.exists():
            txt = p.read_text().strip()
            if txt and not txt.startswith("#"):
                return {
                    "source": "manual_notes",
                    "assignment_num": "",
                    "topic": "Student Lab Notes & Observations",
                    "platform": "Homelab",
                    "context": txt,
                    "images": [],
                    "tags": ["CyberSecurity", "LearningInPublic", "StudentDev"]
                }
                
    # 4. Check unposted assignments
    # Notice: To allow cycling through genuine assignments, we look for assignments
    # where the assignment number or full title isn't in used
    used = get_used_topics()
    for a in assignments:
        key = f"Assignment {a['assignment_num']}: {a['topic']}"
        # If not posted or fewer than 2 posts on this assignment
        if key not in used and a["topic"] not in used:
            ref_summary = " ".join(a["reflections"]) if a["reflections"] else a["topic"]
            return {
                "source": "assignment",
                "assignment_num": a["assignment_num"],
                "topic": a["topic"],
                "category": "Cyber Security & Pentesting",
                "platform": a["platform"],
                "context": ref_summary,
                "labs": a["labs"],
                "images": a["images"],
                "tags": ["CyberSecurity", "EthicalHacking", "TryHackMe", "CyberSecuredIndia", "SafeSkillz"]
            }
            
    # 5. Check Backlog Topics (Rotate diverse non-internship builder posts)
    for b in BACKLOG_TOPICS:
        if b["topic"] not in used:
            return {
                "source": "backlog",
                "assignment_num": b.get("assignment_num", ""),
                "topic": b["topic"],
                "category": b.get("category", "General Engineering"),
                "platform": b["platform"],
                "context": b["context"],
                "images": [],
                "tags": b["tags"]
            }

    # 6. Autonomous Research Engine: Trigger when backlog runs out!
    try:
        import autonomous_researcher
        print("[Detector] Backlog exhausted. Invoking Autonomous Researcher for fresh topic...")
        return autonomous_researcher.research_fresh_topic()
    except Exception as e:
        print(f"[warn] Autonomous research fallback ({e}), rotating back through assignments...")
    if assignments:
        selected = assignments[0]
        ref_summary = " ".join(selected["reflections"]) if selected["reflections"] else selected["topic"]
        return {
            "source": "assignment_rotation",
            "assignment_num": selected["assignment_num"],
            "topic": selected["topic"],
            "category": "Cyber Security & Pentesting",
            "platform": selected["platform"],
            "context": ref_summary,
            "labs": selected["labs"],
            "images": selected["images"],
            "tags": ["CyberSecurity", "EthicalHacking", "TryHackMe", "CyberSecuredIndia", "SafeSkillz"]
        }
        
    # 7. Ultimate loop back through BACKLOG
    selected_b = BACKLOG_TOPICS[0]
    return {
        "source": "backlog_rotation",
        "assignment_num": selected_b.get("assignment_num", ""),
        "topic": selected_b["topic"],
        "category": selected_b.get("category", "General Engineering"),
        "platform": selected_b["platform"],
        "context": selected_b["context"],
        "images": [],
        "tags": selected_b["tags"]
    }

if __name__ == "__main__":
    t = detect_daily_topic()
    print("Detected topic:")
    print(json.dumps(t, indent=2))
