import subprocess
import sys

HOSTKEY = 'SHA256:Spg7rum7lHwouvgx6d2YtcxYMK0xr5e2pmTDQBfGARU'
PW = 'arush'
HOST = 'arush@192.168.0.100'

def run_pi(cmd_str):
    cmd = ['plink', '-batch', '-hostkey', HOSTKEY, '-pw', PW, HOST, cmd_str]
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    return res.stdout, res.stderr

if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else "python3 -c 'import pypdf; print(\"pypdf:\", pypdf.__version__)'"
    out, err = run_pi(cmd)
    print("STDOUT:", out)
    if err:
        print("STDERR:", err)
