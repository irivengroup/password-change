#!/usr/bin/env python3
"""Project schema validation for changepassword."""

from pathlib import Path
import sys
import yaml

VAULT_FILE = Path("inventories/production/group_vars/all/vault.yml")
ACCOUNT_LIST_KEY = "changepassword_local_accounts"
ACCOUNT_NAME_KEY = "username"

if not VAULT_FILE.exists():
    print("Missing inventories/production/group_vars/all/vault.yml", file=sys.stderr)
    sys.exit(1)

data = yaml.safe_load(VAULT_FILE.read_text(encoding="utf-8")) or {}
accounts = data.get(ACCOUNT_LIST_KEY, [])

if accounts and not isinstance(accounts, list):
    print(f"{ACCOUNT_LIST_KEY} must be a list", file=sys.stderr)
    sys.exit(1)

allowed = {
    ACCOUNT_NAME_KEY,
    "password",
    "state",
    "expire",
}

for idx, account in enumerate(accounts):
    if not isinstance(account, dict):
        print(f"{ACCOUNT_LIST_KEY}[{idx}] must be a mapping", file=sys.stderr)
        sys.exit(1)

    unknown = set(account) - allowed
    if unknown:
        print(f"{ACCOUNT_LIST_KEY}[{idx}] has unsupported keys: {sorted(unknown)}", file=sys.stderr)
        sys.exit(1)

    if not account.get(ACCOUNT_NAME_KEY):
        print(f"{ACCOUNT_LIST_KEY}[{idx}].{ACCOUNT_NAME_KEY} is required", file=sys.stderr)
        sys.exit(1)

    if "password" not in account:
        print(f"{ACCOUNT_LIST_KEY}[{idx}].password is required", file=sys.stderr)
        sys.exit(1)

    if account.get("state") not in (None, "locked", "unlocked"):
        print(f"{ACCOUNT_LIST_KEY}[{idx}].state must be locked or unlocked", file=sys.stderr)
        sys.exit(1)

print("Project schema validation OK")
