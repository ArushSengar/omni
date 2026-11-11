import sys
import subprocess

HOSTKEY = 'SHA256:Spg7rum7lHwouvgx6d2YtcxYMK0xr5e2pmTDQBfGARU'
PW = 'arush'
HOST = 'arush@192.168.0.100'

def run_remote(bash_cmd):
    cmd = ['plink', '-batch', '-hostkey', HOSTKEY, '-pw', PW, HOST, 'bash -s']
    clean_cmd = bash_cmd.replace('\r\n', '\n').replace('\r', '\n')
    res = subprocess.run(cmd, input=clean_cmd.encode('utf-8'), capture_output=True)
    return res.returncode, res.stdout.decode('utf-8', errors='replace'), res.stderr.decode('utf-8', errors='replace')

if __name__ == '__main__':
    if len(sys.argv) > 1:
        bash_script = ' '.join(sys.argv[1:])
    else:
        bash_script = sys.stdin.read()
    code, out, err = run_remote(bash_script)
    if out:
        print(out, end='')
    if err:
        print(err, file=sys.stderr, end='')
    sys.exit(code)

