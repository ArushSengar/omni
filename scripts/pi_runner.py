import subprocess
import sys

def run_pi(cmd, timeout=30):
    plink_cmd = [
        "plink", "-batch",
        "-hostkey", "SHA256:Spg7rum7lHwouvgx6d2YtcxYMK0xr5e2pmTDQBfGARU",
        "-pw", "arush",
        "arush@192.168.0.100",
        cmd
    ]
    proc = subprocess.run(plink_cmd, capture_output=True, text=True, timeout=timeout)
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = " ".join(sys.argv[1:])
        code, out, err = run_pi(cmd)
        if out:
            print(out)
        if err:
            print("STDERR:", err, file=sys.stderr)
        sys.exit(code)

