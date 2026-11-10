import subprocess
import sys
from pathlib import Path

HOSTKEY = "SHA256:Spg7rum7lHwouvgx6d2YtcxYMK0xr5e2pmTDQBfGARU"
PW = "arush"
HOST = "arush@192.168.0.100"

def scp(local_file, remote_path):
    cmd = [
        "pscp", "-batch",
        "-hostkey", HOSTKEY,
        "-pw", PW,
        str(local_file),
        f"{HOST}:{remote_path}"
    ]
    print(f"Deploying {local_file} -> {remote_path}...")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"ERROR: {res.stderr}")
        sys.exit(1)
    print("  Done.")

def ssh(command):
    cmd = [
        "plink", "-batch",
        "-hostkey", HOSTKEY,
        "-pw", PW,
        HOST,
        command
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    return res.returncode, res.stdout, res.stderr

def main():
    root = Path(__file__).resolve().parent.parent

    # 1. Transfer settings.py and views.py
    scp(root / "omni_hub" / "omni_hub" / "settings.py", "/home/arush/omni_hub/omni_hub/settings.py")
    scp(root / "omni_hub" / "growth" / "views.py", "/home/arush/omni_hub/growth/views.py")

    # 2. Transfer omni_vault_engine.py
    scp(root / "omni_hub" / "growth" / "omni_vault_engine.py", "/home/arush/omni_hub/growth/omni_vault_engine.py")

    # 3. Transfer hermes_omnivault.py
    scp(root / "hermes" / "scripts" / "hermes_omnivault.py", "/home/arush/hermes_omnivault.py")

    # 4. Ensure skill directory exists on Pi and transfer SKILL.md
    ssh("mkdir -p /home/arush/.hermes/skills/omnivault-memory")
    scp(root / "hermes" / "skills" / "omnivault-memory" / "SKILL.md", "/home/arush/.hermes/skills/omnivault-memory/SKILL.md")

    # 5. Make executable and update /usr/local/bin/hermes-omnivault
    code, out, err = ssh("chmod +x /home/arush/hermes_omnivault.py && echo arush | sudo -S cp /home/arush/hermes_omnivault.py /usr/local/bin/hermes-omnivault && echo arush | sudo -S chmod +x /usr/local/bin/hermes-omnivault")
    print("Permissions and symlink updated.")

    # 6. Run manage.py check on Pi
    code, out, err = ssh("python3 /home/arush/omni_hub/manage.py check")
    print("Django Check output:", out)
    if code != 0:
        print("Check FAILED:", err)
        sys.exit(1)

    # 7. Restart omni-hub.service
    print("Restarting omni-hub.service...")
    code, out, err = ssh("echo arush | sudo -S systemctl restart omni-hub.service")
    code, out, err = ssh("systemctl is-active omni-hub.service")
    print("omni-hub.service status:", out)

if __name__ == "__main__":
    main()
