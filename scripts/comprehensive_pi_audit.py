import subprocess

HOSTKEY = 'SHA256:Spg7rum7lHwouvgx6d2YtcxYMK0xr5e2pmTDQBfGARU'
PW = 'arush'
HOST = 'arush@192.168.0.100'

script = r"""
echo '=== 1. FIREWALL & IPTABLES ==='
which ufw || echo 'no ufw'
sudo iptables -L -n | head -n 15

echo ''
echo '=== 2. HERMES STATE.DB TABLES & ROW COUNTS ==='
python3 -c "
import sqlite3
conn = sqlite3.connect('/home/arush/.hermes/state.db')
c = conn.cursor()
c.execute(\"SELECT name FROM sqlite_master WHERE type='table';\")
tables = [r[0] for r in c.fetchall()]
print('Tables in state.db count:', len(tables))
for t in tables[:15]:
    try:
        c.execute(f'SELECT count(*) FROM {t};')
        print(f'  {t}: {c.fetchone()[0]} rows')
    except Exception as e:
        print(f'  {t}: {e}')
conn.close()
"

echo ''
echo '=== 3. TOP RAM CONSUMERS ==='
ps -eo pid,user,%mem,rss,cmd --sort=-%mem | head -n 12

echo ''
echo '=== 4. HERMES SESSIONS & DISK USAGE ==='
du -sh /home/arush/.hermes/sessions /home/arush/.hermes/logs /home/arush/.hermes/memories /home/arush/.hermes/tools 2>/dev/null

echo ''
echo '=== 5. CHECK COMPOSIO PERMISSIONS ==='
ls -l /home/arush/.composio_social_config.json

echo ''
echo '=== 6. CHECK DJANGO RUNSERVER RAM ==='
ps aux | grep manage.py | grep -v grep
"""

cmd = ['plink', '-batch', '-hostkey', HOSTKEY, '-pw', PW, HOST, 'bash -s']
res = subprocess.run(cmd, input=script.encode('utf-8'), capture_output=True)
print(res.stdout.decode('utf-8', errors='replace'))
if res.stderr:
    print("STDERR:", res.stderr.decode('utf-8', errors='replace'))

