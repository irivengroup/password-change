#!/usr/bin/env python3
"""Static hardening checks for the changepassword project."""

from pathlib import Path
import re
import sys
import yaml

ROOT = Path(__file__).resolve().parents[1]
SELF = Path(__file__).resolve()

FORBIDDEN_PATTERNS = {
    "item.changepassword_target_account": "account objects must use item.username",
    "account.changepassword_target_account": "account objects must use account.username",
    "map(attribute='changepassword_target_account')": "account attribute mapping must use username",
    "selectattr('changepassword_target_account'": "account attribute filtering must use username",
    "rejectattr('changepassword_target_account'": "account attribute filtering must use username",
    "{changepassword_target_account:": "flow account dictionaries must use username",
}

failed = False

for path in ROOT.rglob("*"):
    if not path.is_file() or path.resolve() == SELF:
        continue
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        continue

    for pattern, reason in FORBIDDEN_PATTERNS.items():
        if pattern in text:
            print(f"{path.relative_to(ROOT)}: forbidden pattern {pattern!r}: {reason}", file=sys.stderr)
            failed = True

    if re.search(r"(?m)^\s*-\s*changepassword_target_account\s*:", text):
        print(f"{path.relative_to(ROOT)}: account list item still uses changepassword_target_account", file=sys.stderr)
        failed = True

for path in list(ROOT.rglob("*.yml")) + list(ROOT.rglob("*.yaml")):
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"{path.relative_to(ROOT)}: YAML parse error: {exc}", file=sys.stderr)
        failed = True
        continue

    def scan(obj):
        global failed
        if isinstance(obj, dict):
            accounts = obj.get("changepassword_local_accounts")
            if isinstance(accounts, list):
                for index, account in enumerate(accounts):
                    if not isinstance(account, dict):
                        print(f"{path.relative_to(ROOT)}: changepassword_local_accounts[{index}] is not a dict", file=sys.stderr)
                        failed = True
                        continue
                    if "changepassword_target_account" in account:
                        print(f"{path.relative_to(ROOT)}: changepassword_local_accounts[{index}] uses legacy key", file=sys.stderr)
                        failed = True
                    if "username" not in account:
                        print(f"{path.relative_to(ROOT)}: changepassword_local_accounts[{index}] missing username", file=sys.stderr)
                        failed = True
            for value in obj.values():
                scan(value)
        elif isinstance(obj, list):
            for value in obj:
                scan(value)

    scan(data)

sys.exit(1 if failed else 0)
