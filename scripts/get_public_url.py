import subprocess
import sys

def get_remote_public_url(pi_host="192.168.0.100", user="arush"):
    cmd = [
        "plink", "-batch",
        "-hostkey", "SHA256:Spg7rum7lHwouvgx6d2YtcxYMK0xr5e2pmTDQBfGARU",
        "-pw", "arush",
        f"{user}@{pi_host}",
        "cat ~/.omniroute/public_url.txt 2>/dev/null"
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    url = res.stdout.strip()
    return url

if __name__ == "__main__":
    url = get_remote_public_url()
    if url.startswith("https://"):
        print(f"Current OmniRoute Public URL: {url}")
        print(f"OpenAI Base URL: {url}/v1")
    else:
        print("Could not retrieve public URL. Check if omniroute-tunnel.service is running.")
        sys.exit(1)
