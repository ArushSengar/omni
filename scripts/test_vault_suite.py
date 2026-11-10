import subprocess
import json
import sys

HOSTKEY = "SHA256:Spg7rum7lHwouvgx6d2YtcxYMK0xr5e2pmTDQBfGARU"
PW = "arush"
HOST = "arush@192.168.0.100"

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

def run_test():
    print("=== 1. Testing hermes-omnivault status ===")
    code, out, err = ssh("hermes-omnivault status --json")
    print(out)
    assert code == 0, f"Status failed: {err}"
    status_data = json.loads(out)
    assert status_data["status"] == "ok"
    print(f"Status OK: Temp={status_data['system']['temp_c']}C, RAM={status_data['system']['memory']['percent']}%")

    print("\n=== 2. Testing hermes-omnivault wallet ===")
    code, out, err = ssh("hermes-omnivault wallet --json")
    print(out)
    assert code == 0, f"Wallet failed: {err}"
    wallet_data = json.loads(out)
    assert wallet_data["status"] == "ok"
    print(f"Wallet OK: Providers={wallet_data['wallet']['active_providers']}/11, Savings=${wallet_data['wallet']['cost_saved_usd']}")

    print("\n=== 3. Testing SSRF Rejections ===")
    for bad_url in ["http://127.0.0.1:8000", "http://0.0.0.0:8000", "http://169.254.169.254", "http://localhost:8000"]:
        code, out, err = ssh(f"hermes-omnivault ingest-url {bad_url} --json")
        res = json.loads(out)
        assert res["status"] == "error", f"Should have blocked {bad_url}"
        print(f"SSRF blocked: {bad_url} -> {res['message']}")

    print("\n=== 4. Testing Deletion & Image Disk Unlink ===")
    pi_script = """python3 - << 'EOF'
import os, sys
sys.path.insert(0, "/home/arush/omni_hub")
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "omni_hub.settings")
django.setup()
from django.conf import settings
from growth.models import VaultResource
from django.test import RequestFactory
from growth.views import api_vault_delete
import json

# Create dummy media file
media_dir = os.path.join(settings.MEDIA_ROOT, "vault_uploads")
os.makedirs(media_dir, exist_ok=True)
dummy_img = os.path.join(media_dir, "test_unlink_dummy.jpg")
with open(dummy_img, "w") as f:
    f.write("dummy image data")

# Create test resource
res = VaultResource.objects.create(
    title="Temporary Unlink Test Item",
    category="Developer & APIs",
    one_liner="Test item for unlink verification",
    image_path=dummy_img
)
res_id = res.id

# Verify file exists
assert os.path.exists(dummy_img), "Dummy image was not created"

# Call api_vault_delete
rf = RequestFactory()
req = rf.post('/api/vault/delete/', data=json.dumps({"id": res_id}), content_type="application/json")
resp = api_vault_delete(req)
resp_data = json.loads(resp.content.decode('utf-8'))
print("Delete response:", resp_data)

# Verify resource deleted from DB
assert not VaultResource.objects.filter(id=res_id).exists(), "Resource still in DB"

# Verify file unlinked from disk
assert not os.path.exists(dummy_img), "Image file was NOT unlinked from disk!"
print("SUCCESS: VaultResource deleted and image file safely unlinked from disk.")
EOF
"""
    code, out, err = ssh(pi_script)
    print(out)
    if err and "warning" not in err.lower():
        print("STDERR:", err)
    assert code == 0, f"Unlink test failed: {err}"

    # Also clean up any 'Hermes URL Ingest' or test remnants
    cleanup_cmd = """python3 - << 'EOF'
import os, sys, django
sys.path.insert(0, "/home/arush/omni_hub")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "omni_hub.settings")
django.setup()
from growth.models import VaultResource
count, _ = VaultResource.objects.filter(title="Hermes URL Ingest").delete()
print(f"Cleaned up {count} test entries.")
EOF
"""
    code, out, err = ssh(cleanup_cmd)
    print(out)

    print("\n=== 5. Final Vault Search Verification ===")
    code, out, err = ssh("hermes-omnivault search CyberChef --json")
    print(out)
    search_data = json.loads(out)
    assert search_data["status"] == "ok"
    assert search_data["count"] > 0
    print(f"Search OK: Found {search_data['count']} CyberChef tools in OmniVault.")

    print("\nALL VERIFICATION TESTS PASSED SUCCESSFULLY! 🎯")

if __name__ == "__main__":
    run_test()
