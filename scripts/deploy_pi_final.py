import subprocess
import os

HOSTKEY = 'SHA256:Spg7rum7lHwouvgx6d2YtcxYMK0xr5e2pmTDQBfGARU'
PW = 'arush'
HOST = 'arush@192.168.0.100'

def run_pi(cmd_str):
    cmd = ['plink', '-batch', '-hostkey', HOSTKEY, '-pw', PW, HOST, cmd_str]
    res = subprocess.run(cmd, capture_output=True, text=True)
    return res.stdout, res.stderr

print("1. Creating /home/arush/jarvis_roadmap on Pi...")
out, err = run_pi("mkdir -p /home/arush/jarvis_roadmap")
print(out, err)

print("2. Uploading 05_HERMES_TRAINING_AND_CALIBRATION_BLUEPRINT.md...")
local_blueprint = os.path.abspath("jarvis_roadmap/05_HERMES_TRAINING_AND_CALIBRATION_BLUEPRINT.md")
pscp_cmd = ['pscp', '-batch', '-hostkey', HOSTKEY, '-pw', PW, local_blueprint, f'{HOST}:/home/arush/jarvis_roadmap/05_HERMES_TRAINING_AND_CALIBRATION_BLUEPRINT.md']
res = subprocess.run(pscp_cmd, capture_output=True, text=True)
print("PSCP stdout:", res.stdout)
print("PSCP stderr:", res.stderr)

print("3. Updating 2026-11-11_career_sentinel_and_jobbot_upgrade.md...")
update_mem_doc = """
cat << 'EOF' >> /home/arush/.hermes/memories/2026-11-11_career_sentinel_and_jobbot_upgrade.md

## 4. Final Updates: Dashboard HTML Zero-Error Fix & Hermes Training Blueprint (16:45 IST)
1. **VS Code & HTML Validation (Zero Errors Achieved)**:
   - Fixed all 9 red syntax/parse errors in `omni_hub/growth/templates/growth/dashboard.html`.
   - Single-quoted template parameters in event handlers (`'{{ r.id }}'`, `'{{ job.id }}'`) to eliminate TypeScript parser syntax breaks.
   - Cleaned up raw comparison operators inside HTML attributes by creating `@property def is_high_match` on `JobOpportunity` model.
   - Replaced empty `src=""` on `<iframe id="report-iframe">` with valid `src="about:blank"`.
   - Verified with `npx htmlhint`: 0 errors.

2. **Hermes Future Training & Calibration Architecture Ready**:
   - Deployed `jarvis_roadmap/05_HERMES_TRAINING_AND_CALIBRATION_BLUEPRINT.md`.
   - Curriculum defined across 3 domains: OPSWAT Cyber, Reverse Engineering & SOC, Human Builder Social Voice.
   - Automated dataset extraction script designed for SQLite and state.db.
   - Staged for future fine-tuning execution (Unsloth Cloud LoRA / Local Prompt Distillation) when Arush requests.
EOF
"""
run_pi(update_mem_doc)

print("4. Updating MEMORY.md...")
update_memory_md = """
cat << 'EOF' >> /home/arush/.hermes/memories/MEMORY.md

§
God-Mode v5.3: UI Polish, RAM Hardening & Hermes Training Preparation (November 11, 2026):
- DASHBOARD HTML 9 RED ERRORS RESOLVED:
  * Resolved all 9 VS Code template and syntax errors in omni_hub/growth/templates/growth/dashboard.html.
  * Single-quoted template expressions in event handlers ('{{ r.id }}', '{{ job.id }}').
  * Converted raw angle comparison (>= 80) into clean Django model property (@property def is_high_match on JobOpportunity).
  * Replaced empty src="" on <iframe id="report-iframe"> with valid src="about:blank".
  * Verified with npx htmlhint (0 errors) and W3C compliance.
- PI SYSTEM-WIDE RAM & STABILITY TUNING:
  * OmniRoute memory capped to 768MB with systemd cgroups (RSS down to 601MB from 729MB, -128MB RAM freed).
  * Django DEBUG=False in production eliminating query accumulation memory leak.
  * SQLite WAL mode, NORMAL synchronous, 64MB cache, 256MB mmap.
  * Self-healing watchdog v4.1 memory check auto-flushes cache if RAM >= 90%.
  * Playwright --disable-dev-shm-usage prevents shared memory crashes.
  * Total Pi available RAM increased to 2.1 GiB with 0 Bytes swap used.
- HERMES FUTURE TRAINING ROADMAP (BLUEPRINT READY):
  * Established architecture in ~/jarvis_roadmap/05_HERMES_TRAINING_AND_CALIBRATION_BLUEPRINT.md.
  * 3 Core Curriculum Domains: OPSWAT & Enterprise Cyber, Reverse Engineering & SOC, Human Builder Social Voice (120-180 words, no AI buzzwords).
  * Dataset extraction pipeline configured from omni_hub/db.sqlite3 and state.db.
  * 10-Point automated verification suite for post-training validation.
  * Staged for future execution (Cloud LoRA / Unsloth via Colab or local prompt distillation).
EOF
"""
run_pi(update_memory_md)

print("Done updating memory files.")

