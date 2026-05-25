#!/usr/bin/env python3
"""Validate IRIVEN ChangePassword repository schema and invariants."""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
ACCOUNT_ALLOWED_KEYS = {"username", "password", "state", "expire"}
ACCOUNT_STATES = {"locked", "unlocked"}
USERNAME_RE = re.compile(r"^[a-z_][a-z0-9_-]{0,31}$|^root$")
HASH_RE = re.compile(r"^\$(5|6)\$(rounds=[0-9]+\$)?[^$]{1,16}\$.+")
FORBIDDEN_ACCOUNT_KEYS = {
    "password_hash", "password_plain", "manage_password", "shell", "groups",
    "append", "home", "uid", "gid", "comment", "create_home", "system", "aging",
}


def read_yaml(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    if text.startswith("$ANSIBLE_VAULT;"):
        return None
    return yaml.safe_load(text) or {}


def validate_accounts(path: Path, errors: list[str]) -> None:
    data = read_yaml(path)
    if data is None or not isinstance(data, dict):
        return
    accounts = data.get("changepassword_local_accounts", [])
    if accounts is None:
        return
    if not isinstance(accounts, list):
        errors.append(f"{path}: changepassword_local_accounts must be a list of dictionaries")
        return
    seen: set[str] = set()
    for index, account in enumerate(accounts):
        label = f"{path}: changepassword_local_accounts[{index}]"
        if not isinstance(account, dict):
            errors.append(f"{label}: item must be a dictionary")
            continue
        unknown = set(account) - ACCOUNT_ALLOWED_KEYS
        if unknown:
            errors.append(f"{label}: unsupported keys: {sorted(unknown)}")
        forbidden = set(account) & FORBIDDEN_ACCOUNT_KEYS
        if forbidden:
            errors.append(f"{label}: forbidden keys: {sorted(forbidden)}")
        changepassword_target_account = account.get("username")
        if not isinstance(changepassword_target_account, str) or not changepassword_target_account.strip():
            errors.append(f"{label}: changepassword_target_account is required")
        elif not USERNAME_RE.match(changepassword_target_account):
            errors.append(f"{label}: invalid changepassword_target_account format: {changepassword_target_account!r}")
        elif changepassword_target_account in seen:
            errors.append(f"{label}: duplicate changepassword_target_account: {changepassword_target_account}")
        else:
            seen.add(changepassword_target_account)
        password = account.get("password")
        if not isinstance(password, str) or not password.strip():
            errors.append(f"{label}: password is mandatory")
        elif password.startswith("$") and not HASH_RE.match(password):
            errors.append(f"{label}: password hash must be SHA256/SHA512 crypt ($5$ or $6$)")
        state = account.get("state")
        if state is not None and state not in ACCOUNT_STATES:
            errors.append(f"{label}: state must be one of {sorted(ACCOUNT_STATES)}")
        expire = account.get("expire")
        if expire is not None and not isinstance(expire, bool):
            errors.append(f"{label}: expire must be boolean")


def validate_defaults(errors: list[str]) -> None:
    path = ROOT / "roles/changepassword/defaults/main.yml"
    defaults = read_yaml(path)
    if not isinstance(defaults, dict):
        errors.append(f"{path}: defaults must be a mapping")
        return
    expected_values = {
        "changepassword_hash_algorithm": "sha512",
        "changepassword_hash_salt_mode": "hmac_machine_id",
        "changepassword_audit_file": "/var/log/ansible/changepassword.json",
        "changepassword_audit_file_mode": "0600",
        "changepassword_audit_dir_mode": "0750",
    }
    for key, expected in expected_values.items():
        if defaults.get(key) != expected:
            errors.append(f"{path}: {key} must be {expected!r}")
    if defaults.get("changepassword_set_aging") is not False:
        errors.append(f"{path}: changepassword_set_aging must default to false")
    for key in (
        "changepassword_min_days", "changepassword_max_days",
        "changepassword_warn_days", "changepassword_inactive_days",
    ):
        if defaults.get(key) is not None:
            errors.append(f"{path}: {key} must default to null")
    if int(defaults.get("changepassword_min_hash_rounds", 0)) < 500000:
        errors.append(f"{path}: minimum hash rounds must be >= 500000")
    if int(defaults.get("changepassword_default_hash_rounds", 0)) < int(defaults.get("changepassword_min_hash_rounds", 0)):
        errors.append(f"{path}: default hash rounds must be >= minimum hash rounds")
    if int(defaults.get("changepassword_min_hmac_secret_length", 0)) < 32:
        errors.append(f"{path}: HMAC secret minimum length must be >= 32")
    fallback = defaults.get("changepassword_default_hmac_salt_secret", "")
    if not isinstance(fallback, str) or len(fallback) != 60:
        errors.append(f"{path}: default HMAC fallback secret must be exactly 60 characters")
    elif not (any(c.isupper() for c in fallback) and any(c.islower() for c in fallback) and any(c.isdigit() for c in fallback) and any(not c.isalnum() for c in fallback)):
        errors.append(f"{path}: default HMAC fallback secret must meet complexity requirements")


def validate_static_files(errors: list[str]) -> None:
    required_files = [
        "roles/changepassword/tasks/tasks.d/apply.yml",
        "roles/changepassword/tasks/tasks.d/shadow.yml",
        "roles/changepassword/tasks/tasks.d/audit.yml",
        "roles/changepassword/molecule/default/molecule.yml",
        ".github/workflows/ci.yml",
        ".github/workflows/release.yml",
        "scripts/validate_project_schema.py",
        ".gitleaks.toml",
    ]
    for rel in required_files:
        if not (ROOT / rel).is_file():
            errors.append(f"missing required file: {rel}")
    for rel in (
        "roles/changepassword/tasks/tasks.d/apply_password.yml",
        "roles/changepassword/tasks/tasks.d/shadow_precheck.yml",
    ):
        if (ROOT / rel).exists():
            errors.append(f"obsolete file must not exist: {rel}")
    ansible_cfg = (ROOT / "ansible.cfg").read_text(encoding="utf-8")
    for expected in ("host_key_checking = True", "display_args_to_stdout = False", "allow_world_readable_tmpfiles = False"):
        if expected not in ansible_cfg:
            errors.append(f"ansible.cfg: missing {expected}")
    normalize = (ROOT / "roles/changepassword/tasks/tasks.d/normalize.yml").read_text(encoding="utf-8")
    if "inventory_hostname" in normalize:
        errors.append("normalize.yml: salt generation must not depend on inventory_hostname")
    audit = (ROOT / "roles/changepassword/tasks/tasks.d/audit.yml").read_text(encoding="utf-8")
    for forbidden in ("final_password_hash", "generated_salt", "effective_hmac", "hmac_salt_secret"):
        if forbidden in audit:
            errors.append(f"audit.yml: forbidden sensitive token found: {forbidden}")
    for required in ("to_json", "schema_version", "timestamp_utc", "target_user", "execution_mode", "checksum"):
        if required not in audit:
            errors.append(f"audit.yml: missing audit field/control: {required}")


def main() -> None:
    errors: list[str] = []
    for path in sorted((ROOT / "inventories").rglob("vault.yml*")):
        validate_accounts(path, errors)
    for path in sorted((ROOT / "roles/changepassword/molecule").rglob("*.yml")):
        validate_accounts(path, errors)
    validate_defaults(errors)
    validate_static_files(errors)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        raise SystemExit(1)
    print("IRIVEN ChangePassword schema validation passed")


if __name__ == "__main__":
    main()
