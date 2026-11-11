import subprocess

HOSTKEY = 'SHA256:Spg7rum7lHwouvgx6d2YtcxYMK0xr5e2pmTDQBfGARU'
PW = 'arush'
HOST = 'arush@192.168.0.100'

def run_pi(cmd_str):
    cmd = ['plink', '-batch', '-hostkey', HOSTKEY, '-pw', PW, HOST, cmd_str]
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    return res.stdout, res.stderr

try:
    out, err = run_pi("/home/arush/.local/bin/hermes chat -q 'hi' -m hermes-fast -Q --oneshot --reasoning none")
    print("STDOUT:", out)
    if err:
        print("STDERR:", err)
except Exception as e:
    print("Exception:", e)
