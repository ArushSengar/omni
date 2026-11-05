#!/usr/bin/env python3
"""
OmniKey Manager - Secure API Key & Quota Management for OmniRoute Gateway.
Compatible with Python 3.8+ on Linux and Windows (via SSH or direct SQLite).
"""

import argparse
import hashlib
import json
import os
import secrets
import sqlite3
import sys
import uuid
import urllib.request
from datetime import datetime, timezone

DB_DEFAULT_PATH = os.path.expanduser("~/.omniroute/storage.sqlite")

def get_connection(db_path=None):
    path = db_path or os.environ.get("OMNIROUTE_DB", DB_DEFAULT_PATH)
    if not os.path.exists(path):
        raise FileNotFoundError(f"OmniRoute database not found at: {path}")
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn

def list_keys(db_path=None):
    conn = get_connection(db_path)
    c = conn.cursor()
    c.execute("""
        SELECT id, name, key_prefix, is_active, model_access_mode,
               allowed_combos, daily_usage_limit_usd, created_at, last_used_at, revoked_at
        FROM api_keys
        ORDER BY created_at DESC
    """)
    rows = c.fetchall()
    conn.close()

    if not rows:
        print("No OmniKeys found in database.")
        return

    print("=" * 110)
    print(f"{'ID':<38} {'NAME':<20} {'PREFIX':<14} {'ACTIVE':<8} {'ACCESS':<8} {'DAILY LIMIT':<12} {'CREATED'}")
    print("=" * 110)
    for r in rows:
        active_str = "YES" if r["is_active"] and not r["revoked_at"] else "REVOKED"
        limit_str = f"${r['daily_usage_limit_usd']:.2f}" if r["daily_usage_limit_usd"] else "Unlimited"
        created_short = r["created_at"][:19] if r["created_at"] else "-"
        print(f"{r['id']:<38} {r['name']:<20} {r['key_prefix']:<14} {active_str:<8} {r['model_access_mode']:<8} {limit_str:<12} {created_short}")
    print("=" * 110)
    print(f"Total OmniKeys: {len(rows)}")

def create_key(name, models=None, combos=None, daily_limit=None, db_path=None):
    conn = get_connection(db_path)
    c = conn.cursor()

    entropy = secrets.token_hex(16)
    tail = secrets.token_hex(4)
    raw_key = f"sk-omni-{entropy}-{tail}"
    key_id = str(uuid.uuid4())
    key_hash = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
    key_prefix = raw_key[:12]
    now = datetime.now(timezone.utc).isoformat()

    model_access_mode = "all" if not models else "restricted"
    allowed_models_json = json.dumps(models or [])
    allowed_combos_json = json.dumps(combos or ["combo/*"])

    sql = """
    INSERT INTO api_keys (
        id, name, key, machine_id, model_access_mode,
        allowed_models, allowed_combos, allowed_connections,
        no_log, created_at, key_prefix, key_hash,
        scopes, is_active, compression_enabled, allow_auto_combos,
        catalog_scope, stream_default_mode, cache_default_mode,
        usage_limit_enabled, daily_usage_limit_usd
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    c.execute(sql, (
        key_id,
        name,
        raw_key,
        "omniroute-manager",
        model_access_mode,
        allowed_models_json,
        allowed_combos_json,
        "[]",
        0,
        now,
        key_prefix,
        key_hash,
        '["chat", "models", "combos", "stream"]',
        1,
        1,
        1,
        "all",
        "legacy",
        "legacy",
        1 if daily_limit else 0,
        daily_limit
    ))
    conn.commit()
    conn.close()

    print("\n[SUCCESS] New OmniKey Generated:")
    print("-" * 60)
    print(f"  Key ID:        {key_id}")
    print(f"  Name:          {name}")
    print(f"  Secret Key:    {raw_key}")
    print(f"  Key Prefix:    {key_prefix}")
    print(f"  Key Hash:      {key_hash}")
    print(f"  Model Access:  {model_access_mode}")
    print(f"  Daily Limit:   {'$' + str(daily_limit) if daily_limit else 'Unlimited'}")
    print("-" * 60)
    print("  * IMPORTANT: Save the Secret Key now. It is used as: Authorization: Bearer <Secret Key>\n")
    return raw_key

def revoke_key(identifier, db_path=None):
    conn = get_connection(db_path)
    c = conn.cursor()
    now = datetime.now(timezone.utc).isoformat()

    c.execute("""
        UPDATE api_keys
        SET is_active = 0, revoked_at = ?
        WHERE id = ? OR key_prefix LIKE ? OR name = ?
    """, (now, identifier, f"{identifier}%", identifier))

    changes = c.rowcount
    conn.commit()
    conn.close()

    if changes > 0:
        print(f"[SUCCESS] Revoked {changes} key(s) matching '{identifier}'.")
    else:
        print(f"[WARNING] No active key found matching identifier '{identifier}'.")

def rotate_key(identifier, db_path=None):
    conn = get_connection(db_path)
    c = conn.cursor()
    c.execute("SELECT id, name FROM api_keys WHERE id = ? OR key_prefix LIKE ? OR name = ?",
              (identifier, f"{identifier}%", identifier))
    row = c.fetchone()
    if not row:
        print(f"[ERROR] Key '{identifier}' not found.")
        conn.close()
        return None

    key_id = row["id"]
    entropy = secrets.token_hex(16)
    tail = secrets.token_hex(4)
    new_raw_key = f"sk-omni-{entropy}-{tail}"
    new_hash = hashlib.sha256(new_raw_key.encode("utf-8")).hexdigest()
    new_prefix = new_raw_key[:12]

    c.execute("""
        UPDATE api_keys
        SET key = ?, key_hash = ?, key_prefix = ?, is_active = 1, revoked_at = NULL
        WHERE id = ?
    """, (new_raw_key, new_hash, new_prefix, key_id))
    conn.commit()
    conn.close()

    print(f"\n[SUCCESS] Key '{row['name']}' (ID: {key_id}) rotated successfully!")
    print(f"  New Secret Key: {new_raw_key}")
    print(f"  New Prefix:     {new_prefix}\n")
    return new_raw_key

def test_key(key, endpoint=None):
    base_url = endpoint or "http://127.0.0.1:20128"
    url = f"{base_url.rstrip('/')}/v1/models"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {key}",
        "User-Agent": "OmniKeyTester/1.0"
    })
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            count = len(data.get("data", []))
            print(f"[SUCCESS] OmniKey authenticated successfully with {base_url}!")
            print(f"HTTP Status: {resp.status} - Total Accessible Models: {count}")
    except urllib.error.HTTPError as e:
        print(f"[FAILED] HTTP Error {e.code}: {e.reason}")
    except Exception as e:
        print(f"[FAILED] Connection Error: {e}")

def main():
    parser = argparse.ArgumentParser(description="OmniRoute OmniKey Management Utility")
    subparsers = parser.add_subparsers(dest="command", help="Sub-commands")

    # list
    subparsers.add_parser("list", help="List all OmniKeys")

    # create
    create_parser = subparsers.add_parser("create", help="Create a new OmniKey")
    create_parser.add_argument("name", help="Human-readable name for the key")
    create_parser.add_argument("--models", nargs="*", help="Restrict to specific model names")
    create_parser.add_argument("--combos", nargs="*", default=["combo/*"], help="Allowed combos (default: combo/*)")
    create_parser.add_argument("--daily-limit", type=float, help="Daily USD budget limit")
    create_parser.add_argument("--db", help="Path to storage.sqlite")

    # revoke
    revoke_parser = subparsers.add_parser("revoke", help="Revoke an existing OmniKey")
    revoke_parser.add_argument("identifier", help="Key ID, prefix, or name")
    revoke_parser.add_argument("--db", help="Path to storage.sqlite")

    # rotate
    rotate_parser = subparsers.add_parser("rotate", help="Rotate an existing OmniKey secret")
    rotate_parser.add_argument("identifier", help="Key ID, prefix, or name")
    rotate_parser.add_argument("--db", help="Path to storage.sqlite")

    # test
    test_parser = subparsers.add_parser("test", help="Test an OmniKey against an endpoint")
    test_parser.add_argument("key", help="The raw OmniKey secret string")
    test_parser.add_argument("--endpoint", default="http://127.0.0.1:20128", help="OmniRoute base URL")

    args = parser.parse_args()

    if args.command == "list":
        list_keys()
    elif args.command == "create":
        create_key(args.name, models=args.models, combos=args.combos, daily_limit=args.daily_limit, db_path=args.db)
    elif args.command == "revoke":
        revoke_key(args.identifier, db_path=args.db)
    elif args.command == "rotate":
        rotate_key(args.identifier, db_path=args.db)
    elif args.command == "test":
        test_key(args.key, endpoint=args.endpoint)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

