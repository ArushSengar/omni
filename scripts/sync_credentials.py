#!/usr/bin/env python3
"""
OmniRoute Safe Credential Management & AES-256-GCM Sync Tool
Allows managing provider credentials in OmniRoute storage.sqlite securely.
"""

import os
import sys
import json
import sqlite3
import hashlib
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

STATIC_SALT = b"omniroute-field-encryption-v1"

def derive_key(secret_hex: str) -> bytes:
    return hashlib.scrypt(secret_hex.encode(), salt=STATIC_SALT, n=16384, r=8, p=1, maxmem=0, dklen=32)

def encrypt_value(plaintext: str, key: bytes) -> str:
    iv = os.urandom(16)
    aesgcm = AESGCM(key)
    ct_with_tag = aesgcm.encrypt(iv, plaintext.encode('utf-8'), None)
    ct = ct_with_tag[:-16]
    tag = ct_with_tag[-16:]
    return f"enc:v1:{iv.hex()}:{ct.hex()}:{tag.hex()}"

def decrypt_value(enc_str: str, key: bytes) -> str:
    if not enc_str.startswith("enc:v1:"):
        return enc_str
    parts = enc_str.split(":")
    if len(parts) != 5:
        raise ValueError("Invalid enc:v1 format")
    iv = bytes.fromhex(parts[2])
    ct = bytes.fromhex(parts[3])
    tag = bytes.fromhex(parts[4])
    aesgcm = AESGCM(key)
    pt = aesgcm.decrypt(iv, ct + tag, None)
    return pt.decode('utf-8')

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python sync_credentials.py list-keys <db_path> <secret_hex>")
        print("  python sync_credentials.py encrypt <secret_hex> <plaintext>")
        print("  python sync_credentials.py decrypt <secret_hex> <enc_string>")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "encrypt":
        secret_hex = sys.argv[2]
        plaintext = sys.argv[3]
        key = derive_key(secret_hex)
        print(encrypt_value(plaintext, key))

    elif cmd == "decrypt":
        secret_hex = sys.argv[2]
        enc_string = sys.argv[3]
        key = derive_key(secret_hex)
        print(decrypt_value(enc_string, key))

    elif cmd == "list-keys":
        db_path = sys.argv[2]
        secret_hex = sys.argv[3]
        key = derive_key(secret_hex)
        con = sqlite3.connect(db_path)
        cur = con.cursor()
        print(f"{'Provider':<20} {'Name':<20} {'Status':<10} {'Credential Preview'}")
        print("=" * 70)
        for row in cur.execute("SELECT provider, name, is_active, api_key, access_token FROM provider_connections"):
            p, name, active, ak, at = row
            cred_raw = ak or at or ""
            try:
                dec = decrypt_value(cred_raw, key) if cred_raw.startswith("enc:v1:") else cred_raw
                preview = dec[:10] + "..." if len(dec) > 10 else dec
            except Exception:
                preview = "[Encrypted]"
            print(f"{p:<20} {str(name):<20} {'Active' if active else 'Inactive':<10} {preview}")

if __name__ == "__main__":
    main()

