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

    # 1. Transfer core growth backend files
    scp(root / "omni_hub" / "omni_hub" / "settings.py", "/home/arush/omni_hub/omni_hub/settings.py")
    scp(root / "omni_hub" / "growth" / "views.py", "/home/arush/omni_hub/growth/views.py")
    scp(root / "omni_hub" / "growth" / "urls.py", "/home/arush/omni_hub/growth/urls.py")
    scp(root / "omni_hub" / "growth" / "models.py", "/home/arush/omni_hub/growth/models.py")
    scp(root / "omni_hub" / "growth" / "omni_vault_engine.py", "/home/arush/omni_hub/growth/omni_vault_engine.py")
    scp(root / "omni_hub" / "vault_ingest.py", "/home/arush/omni_hub/vault_ingest.py")
    scp(root / "hermes" / "scripts" / "hermes_omnivault.py", "/home/arush/hermes_omnivault.py")

    # 2. Transfer templates
    scp(root / "omni_hub" / "growth" / "templates" / "growth" / "vault_dashboard.html", "/home/arush/omni_hub/growth/templates/growth/vault_dashboard.html")
    scp(root / "omni_hub" / "growth" / "templates" / "growth" / "dashboard.html", "/home/arush/omni_hub/growth/templates/growth/dashboard.html")

    # 3. Transfer jobbot_engine.py & jobbot_sentinel.py
    scp(root / "omni_hub" / "growth" / "jobbot_engine.py", "/home/arush/omni_hub/growth/jobbot_engine.py")
    scp(root / "omni_hub" / "growth" / "jobbot_engine.py", "/home/arush/jobbot_engine.py")
    scp(root / "hermes" / "scripts" / "jobbot_sentinel.py", "/home/arush/jobbot_sentinel.py")
    scp(root / "hermes" / "scripts" / "jobbot_sentinel.py", "/home/arush/.hermes/scripts/jobbot_sentinel.py")

    # 4. Transfer growth sentinel, copywriters, activity detector, x_daily_post, growth_reporter_email
    scp(root / "hermes" / "scripts" / "omni_growth_sentinel.py", "/home/arush/omni_growth_sentinel.py")
    scp(root / "hermes" / "scripts" / "omni_growth_sentinel.py", "/home/arush/.hermes/scripts/omni_growth_sentinel.py")
    scp(root / "hermes" / "scripts" / "linkedin_activity_detector.py", "/home/arush/linkedin_activity_detector.py")
    scp(root / "hermes" / "scripts" / "linkedin_activity_detector.py", "/home/arush/.hermes/scripts/linkedin_activity_detector.py")
    scp(root / "hermes" / "scripts" / "linkedin_collage_generator.py", "/home/arush/linkedin_collage_generator.py")
    scp(root / "hermes" / "scripts" / "linkedin_collage_generator.py", "/home/arush/.hermes/scripts/linkedin_collage_generator.py")
    scp(root / "hermes" / "scripts" / "linkedin_daily_post.py", "/home/arush/linkedin_daily_post.py")
    scp(root / "hermes" / "scripts" / "linkedin_daily_post.py", "/home/arush/.hermes/scripts/linkedin_daily_post.py")
    scp(root / "hermes" / "scripts" / "x_daily_post.py", "/home/arush/x_daily_post.py")
    scp(root / "hermes" / "scripts" / "x_daily_post.py", "/home/arush/.hermes/scripts/x_daily_post.py")
    scp(root / "hermes" / "scripts" / "growth_reporter_email.py", "/home/arush/growth_reporter_email.py")
    scp(root / "hermes" / "scripts" / "growth_reporter_email.py", "/home/arush/.hermes/scripts/growth_reporter_email.py")

    # 5. Make scripts executable
    ssh("chmod +x /home/arush/jobbot_sentinel.py /home/arush/omni_growth_sentinel.py /home/arush/x_daily_post.py /home/arush/growth_reporter_email.py /home/arush/.hermes/scripts/*.py")

    # 6. Run manage.py check and migrate on Pi
    code, out, err = ssh("python3 /home/arush/omni_hub/manage.py check")
    print("Django Check output:", out)
    if code != 0:
        print("Check FAILED:", err)
        sys.exit(1)

    code, out, err = ssh("python3 /home/arush/omni_hub/manage.py migrate")
    print("Django Migrate output:", out)
    if code != 0:
        print("Migrate note:", err)

    # 6.5. Run dynamic vault clean & normalize migration
    scp(root / "scripts" / "clean_and_normalize_vault.py", "/home/arush/clean_and_normalize_vault.py")
    print("Running dynamic vault normalization on Pi...")
    code, out, err = ssh("python3 /home/arush/clean_and_normalize_vault.py")
    print(out)
    if err:
        print("Normalization note:", err)

    # 7. Initial Career Sentinel & JobBot scan on Pi
    print("Executing initial Career Sentinel & JobBot scan on Pi...")
    code, out, err = ssh("python3 /home/arush/jobbot_sentinel.py --min-score 60")
    print(out)
    if code != 0:
        print("JobBot notice:", err)

    # 8. Restart omni-hub.service
    print("Restarting omni-hub.service...")
    code, out, err = ssh("echo arush | sudo -S systemctl restart omni-hub.service")
    code, out, err = ssh("systemctl is-active omni-hub.service")
    print("omni-hub.service status:", out)

if __name__ == "__main__":
    main()
