#!/usr/bin/env python3
from pathlib import Path
import sys
import yaml

vault_file = Path("roles/changepassword/vars/accounts.yml")
if not vault_file.exists():
    print("Missing roles/changepassword/vars/accounts.yml", file=sys.stderr)
    sys.exit(1)

data = yaml.safe_load(vault_file.read_text(encoding="utf-8")) or {}
accounts = data.get("changepassword_local_accounts", [])
if accounts and not isinstance(accounts, list):
    print("changepassword_local_accounts must be a list", file=sys.stderr)
    sys.exit(1)

allowed = {"username", "password", "state", "expire"}
for idx, account in enumerate(accounts):
    if not isinstance(account, dict):
        print(f"changepassword_local_accounts[{idx}] must be a mapping", file=sys.stderr)
        sys.exit(1)
    unknown = set(account) - allowed
    if unknown:
        print(f"changepassword_local_accounts[{idx}] has unsupported keys: {sorted(unknown)}", file=sys.stderr)
        sys.exit(1)
    if not account.get("username"):
        print(f"changepassword_local_accounts[{idx}].changepassword_target_account is required", file=sys.stderr)
        sys.exit(1)
    if "password" not in account:
        print(f"changepassword_local_accounts[{idx}].password is required", file=sys.stderr)
        sys.exit(1)
    if account.get("state") not in (None, "locked", "unlocked"):
        print(f"changepassword_local_accounts[{idx}].state must be locked or unlocked", file=sys.stderr)
        sys.exit(1)

print("Project schema validation OK")
