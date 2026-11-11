import subprocess
import json

HOSTKEY = 'SHA256:Spg7rum7lHwouvgx6d2YtcxYMK0xr5e2pmTDQBfGARU'
PW = 'arush'
HOST = 'arush@192.168.0.100'

def ssh_exec(script_text):
    cmd = ['plink', '-batch', '-hostkey', HOSTKEY, '-pw', PW, HOST, 'bash -s']
    clean_script = script_text.replace('\r\n', '\n').replace('\r', '\n')
    res = subprocess.run(cmd, input=clean_script.encode('utf-8'), capture_output=True)
    return res.returncode, res.stdout.decode('utf-8', errors='replace'), res.stderr.decode('utf-8', errors='replace')

script = """
echo "=== 1. TOP PROCESSES BY MEMORY & CPU ==="
ps aux --sort=-%mem | head -n 15

echo ""
echo "=== 2. SYSTEMD SERVICES STATUS ==="
for svc in omni-hub omniroute omniroute-tunnel hermes-dashboard fan-control; do
    echo -n "$svc: "
    systemctl is-active $svc
done

echo ""
echo "=== 3. PYTHON ENVIRONMENTS & PLAYWRIGHT CHECK ==="
which python3
python3 -c "import sys; print('system python:', sys.version.split()[0])"
python3 -c "import playwright; print('system python has playwright OK')" 2>&1 || echo "system python lacks playwright"
if [ -f /home/arush/.hermes/venv/bin/python ]; then
    /home/arush/.hermes/venv/bin/python -c "import playwright; print('hermes venv has playwright OK')" 2>&1 || echo "hermes venv lacks playwright"
fi

echo ""
echo "=== 4. CRON JOBS DETAILED CHECK ==="
crontab -l

echo ""
echo "=== 5. CHECK RECENT RUNS OF AUTONOMOUS SENTINEL & GROWTH ==="
ls -lht /home/arush/posts/daily/ | head -n 10
tail -n 15 /home/arush/posts/daily/sentinel.log 2>/dev/null

echo ""
echo "=== 6. CHECK FOR DUPLICATE / OBSOLETE FILES IN HOME DIR ==="
ls -1 /home/arush/*watchdog* /home/arush/check* 2>/dev/null

echo ""
echo "=== 7. CHECK EMAIL REPORTING CONFIG ==="
grep -E "EMAIL" /home/arush/.hermes/.env 2>/dev/null || echo "No EMAIL config in ~/.hermes/.env"

echo ""
echo "=== 8. CHECK COMPOSIO SOCIAL CONFIG ==="
cat /home/arush/.composio_social_config.json 2>/dev/null || echo "No composio social config"
"""

if __name__ == '__main__':
    code, out, err = ssh_exec(script)
    print(out)
    if err:
        print("ERRORS:", err)
