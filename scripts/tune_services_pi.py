import subprocess

HOSTKEY = 'SHA256:Spg7rum7lHwouvgx6d2YtcxYMK0xr5e2pmTDQBfGARU'
PW = 'arush'
HOST = 'arush@192.168.0.100'

remote_script = """
cat << 'EOF' > /tmp/omniroute.service
[Unit]
Description=OmniRoute AI Gateway
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=arush
WorkingDirectory=/home/arush
Environment="HOME=/home/arush"
Environment="PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
LimitNOFILE=65536
MemoryHigh=850M
MemoryMax=950M
ExecStart=/usr/bin/omniroute
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo mv /tmp/omniroute.service /etc/systemd/system/omniroute.service
sudo systemctl daemon-reload
sudo systemctl restart omniroute.service
sleep 3
systemctl is-active omniroute.service
"""

cmd = ['plink', '-batch', '-hostkey', HOSTKEY, '-pw', PW, HOST, 'bash -s']
res = subprocess.run(cmd, input=remote_script.encode('utf-8'), capture_output=True)
print(res.stdout.decode('utf-8', errors='replace'))
print(res.stderr.decode('utf-8', errors='replace'))
