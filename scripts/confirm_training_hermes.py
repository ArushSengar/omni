import subprocess

HOSTKEY = 'SHA256:Spg7rum7lHwouvgx6d2YtcxYMK0xr5e2pmTDQBfGARU'
PW = 'arush'
HOST = 'arush@192.168.0.100'

query = (
    "Confirm receipt of the new training roadmap: "
    "~/jarvis_roadmap/05_HERMES_TRAINING_AND_CALIBRATION_BLUEPRINT.md. "
    "Briefly confirm the 3 curriculum domains and your readiness for future fine-tuning."
)

cmd = [
    'plink', '-batch', '-hostkey', HOSTKEY, '-pw', PW, HOST,
    f"/home/arush/.local/bin/hermes chat -q \"{query}\" -m hermes-fast -Q --oneshot --reasoning none"
]

res = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
print("=== HERMES CONFIRMATION ===")
print("STDOUT:\n", res.stdout)
if res.stderr:
    print("STDERR:\n", res.stderr)
