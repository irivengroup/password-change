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
    'map(attribute="changepassword_target_account")': "account attribute mapping must use username",
    "selectattr('changepassword_target_account'": "account attribute filtering must use username",
    'selectattr("changepassword_target_account"': "account attribute filtering must use username",
    "rejectattr('changepassword_target_account'": "account attribute filtering must use username",
    'rejectattr("changepassword_target_account"': "account attribute filtering must use username",
    "{changepassword_target_account:": "flow account dictionaries must use username",
}

AUDIT_SECRET_PATTERNS = [
    "item.password",
    "password_hash",
    "changepassword_hmac_salt_secret",
    "changepassword_hmac_secret_effective",
]

failed = False

def fail(message: str) -> None:
    global failed
    print(message, file=sys.stderr)
    failed = True

def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))

for path in ROOT.rglob("*"):
    if not path.is_file() or path.resolve() == SELF:
        continue

    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        continue

    for pattern, reason in FORBIDDEN_PATTERNS.items():
        if pattern in text:
            fail(f"{rel(path)}: forbidden pattern {pattern!r}: {reason}")

    if re.search(r"(?m)^\s*-\s*changepassword_target_account\s*:", text):
        fail(f"{rel(path)}: account list item still uses changepassword_target_account")

audit_file = ROOT / "roles/changepassword/tasks/tasks.d/audit.yml"
if audit_file.exists():
    audit_text = audit_file.read_text(encoding="utf-8")
    for pattern in AUDIT_SECRET_PATTERNS:
        if pattern in audit_text:
            fail(f"{rel(audit_file)}: audit must not reference secret/hash material pattern {pattern!r}")

for path in list(ROOT.rglob("*.yml")) + list(ROOT.rglob("*.yaml")):
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"{rel(path)}: YAML parse error: {exc}")
        continue

    def scan(obj):
        if isinstance(obj, dict):
            accounts = obj.get("changepassword_local_accounts")
            if isinstance(accounts, list):
                for index, account in enumerate(accounts):
                    if not isinstance(account, dict):
                        fail(f"{rel(path)}: changepassword_local_accounts[{index}] is not a dict")
                        continue
                    if "changepassword_target_account" in account:
                        fail(f"{rel(path)}: changepassword_local_accounts[{index}] uses legacy key")
                    if "username" not in account:
                        fail(f"{rel(path)}: changepassword_local_accounts[{index}] missing username")
                    unknown = set(account) - {"username", "password", "state", "expire"}
                    if unknown:
                        fail(f"{rel(path)}: changepassword_local_accounts[{index}] has unsupported keys: {sorted(unknown)}")
            for value in obj.values():
                scan(value)
        elif isinstance(obj, list):
            for value in obj:
                scan(value)

    scan(data)

sys.exit(1 if failed else 0)
