# 🎓 Hermes Training, Fine-Tuning & Knowledge Calibration Blueprint
**Version**: 1.0 (Architecture & Readiness Specification)  
**Target Entity**: Hermes Autonomous AI Agent (Raspberry Pi 4 Cluster)  
**Primary Human Lead**: Arush Sengar (Galgotias University · B.Tech Cybersecurity & Systems)

---

## 1. Executive Overview & Objectives
Hermes operates as the autonomous brain and executor across Arush's personal computing ecosystem (Master Cockpit on Port 8000, OmniRoute AI Gateway on Port 20128, OmniVault multimodal knowledge repository, and automated LinkedIn/X social growth pipelines).

This blueprint establishes the **training readiness foundation** for future fine-tuning and domain calibration, ensuring Hermes can be trained systematically without guesswork.

```
                    ┌──────────────────────────────────────────────┐
                    │        CURATED TRAINING DATA SOURCES         │
                    └──────────────────────┬───────────────────────┘
                                           │
         ┌─────────────────────────────────┼─────────────────────────────────┐
         │                                 │                                 │
         ▼                                 ▼                                 ▼
┌──────────────────┐             ┌──────────────────┐             ┌──────────────────┐
│ SQLite db.sqlite3│             │ Hermes state.db  │             │ OmniVault & Docs │
│ High-performing  │             │ Arush's command  │             │ OPSWAT, Malware, │
│ posts & metrics  │             │ patterns & style │             │ Lab assignments  │
└────────┬─────────┘             └────────┬─────────┘             └────────┬─────────┘
         │                                │                                │
         └────────────────────────────────┼────────────────────────────────┘
                                          │
                                          ▼
                    ┌──────────────────────────────────────────────┐
                    │      DATASET PREPARATION & FORMATTING        │
                    │   (ShareGPT / Alpaca JSONL Conversation)     │
                    └──────────────────────┬───────────────────────┘
                                          │
                    ┌─────────────────────┴─────────────────────┐
                    │                                           │
                    ▼                                           ▼
      ┌───────────────────────────┐               ┌───────────────────────────┐
      │   PHASE 1: PROMPT TUNING  │               │    PHASE 2: QLORA / LORA  │
      │  Dynamic SOUL.md update   │               │   Fine-tuning base model  │
      │  Few-shot in-context RAG  │               │   (Unsloth / Axolotl)     │
      └───────────────────────────┘               └───────────────────────────┘
```

---

## 2. Core Curriculum Domains for Hermes

### Domain A: OPSWAT & Enterprise Cybersecurity
- **Concepts**: Deep CDR (Content Disarm & Reconstruction), Multiscanning (30+ anti-malware engines), Proactive DLP (Data Loss Prevention), ICAP integration with proxies, Kiosk security, OT/ICS critical infrastructure protection.
- **Tone**: Professional, technical, authoritative yet accessible.

### Domain B: Reverse Engineering, SOC & Offensive Security
- **Concepts**: Ghidra disassembly, x86/ARM64 shellcoding, ELF/PE header analysis, TryHackMe/HackTheBox methodologies, Wireshark packet triage, Suricata IDS rules.
- **Tone**: Hands-on practitioner, step-by-step problem solver, zero fluff.

### Domain C: Human Builder Social Voice (LinkedIn & X)
- **Rules**:
  1. 100% human student builder voice (2nd-year B.Tech, Galgotias University).
  2. Strict ban on AI clichés (*"dive into"*, *"testament"*, *"tapestry"*, *"beacon"*, *"in today's fast-paced world"*).
  3. Actionable numbered structure: Hook $\to$ Technical Problem $\to$ 1-2-3 Concrete Fixes $\to$ Real Impact Metric $\to$ Open Question.
  4. Word count limit: 120–180 words (LinkedIn), 240–270 characters (X/Twitter).

---

## 3. Dataset Generation & Export Strategy

When ready to train, run the export script to extract conversation pairs and learning history into standard training formats:

### Step 1: Export Database Learnings
```python
# scripts/export_training_data.py
import sqlite3, json

# Extract approved posts with engagement >= 2%
conn = sqlite3.connect('/home/arush/omni_hub/db.sqlite3')
cur = conn.cursor()
cur.execute("SELECT title, domain, linkedin_content, twitter_content FROM growth_growthpost WHERE status='PUBLISHED'")
records = cur.fetchall()

dataset = []
for title, domain, li, tw in records:
    dataset.append({
        "instruction": f"Write a high-engagement technical builder post about {title} in the {domain} domain.",
        "input": "",
        "output": li
    })

with open('training_dataset_alpaca.json', 'w') as f:
    json.dump(dataset, f, indent=2)
```

### Step 2: Quality Filtering
- Strip conversational disclaimers.
- Normalize line breaks and remove raw markdown fences.
- Verify token count and remove truncated examples.

---

## 4. Execution Channels (When Arush triggers Phase 2)

| Method | Compute Hardware | Recommended Engine | Turnaround Time |
|---|---|---|---|
| **Tier 1: Cloud LoRA** | Free Google Colab (T4 GPU) or RunPod / Vast.ai ($0.20/hr) | Unsloth (Llama-3.1-8B or Qwen-2.5-7B) | ~45 minutes |
| **Tier 2: Prompt Distillation** | Raspberry Pi 4 (Local CPU) | Dynamic `SOUL.md` injection into OmniRoute Gateway | Instant (< 1s) |
| **Tier 3: GGUF Quantization** | Local Laptop (RTX GPU) | llama.cpp `quantize --q4_k_m` | ~15 minutes |

---

## 5. Automated Verification & Evaluation Suite
Before deploying any fine-tuned checkpoint or system prompt update, Hermes must pass the **10-Point Alignment Test**:
1. Zero AI buzzwords in test generation.
2. Correct syntax formatting for Linux terminal commands.
3. Proper OPSWAT MetaDefender vocabulary usage.
4. Correct tool calling for OmniVault memory ingestion.
5. Character count compliance for X/Twitter ($<280$ chars).
6. Response latency under 3.5 seconds on OmniRoute gateway.

---
*Ready for Phase 2 deployment on Arush's command.*

