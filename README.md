# ChgPassword Ansible

Hardened Ansible role and playbook to rotate **local Linux account passwords**, including `root`.

## Task layout

The role is split into Ansible task blocks instead of one monolithic task file:

```text
roles/ChgPassword/tasks/
├── main.yml            # secured workflow block with rescue/always
├── preflight.yml       # validation blocks
├── normalize.yml       # secret-safe runtime normalization block
├── apply_password.yml  # password state application block
├── aging.yml           # expiration and chage policy block
└── audit.yml           # audit trail block without secrets
```

A custom filter plugin is included:

```text
roles/ChgPassword/filter_plugins/crypto_salt.py
```

It derives a deterministic HMAC salt for SHA512 crypt when plaintext input is explicitly enabled.

## Security posture

Defaults are strict:

- `password_hash` is required by default.
- `password_plain` is rejected by default.
- plaintext mode requires explicit opt-in and a Vault/AWX/secret-manager salt secret.
- salt derivation uses `HMAC-SHA256(secret, prefix:username:inventory_hostname)[:16]`.
- public deterministic salt mode is blocked unless explicitly allowed.
- SHA512 crypt hashes are validated.
- `root` can be changed but cannot be locked unless explicitly allowed.
- account names are regex-validated.
- sensitive operations use `no_log: true`.
- audit logs contain no secret material.
- host key checking is enabled in `ansible.cfg`.

## Recommended usage: precomputed hash

```yaml
change_password_accounts:
  - username: root
    password_hash: "$6$rounds=656000$replaceSalt$replaceWithRealSha512CryptHash"
    expire: false
    state: present
```

Generate a SHA512 password hash offline:

```bash
python3 - <<'PY'
import crypt
import getpass
password = getpass.getpass('Password: ')
print(crypt.crypt(password, crypt.mksalt(crypt.METHOD_SHA512, rounds=656000)))
PY
```

Encrypt variables:

```bash
ansible-vault encrypt inventories/production/group_vars/all.yml
```

Run:

```bash
ansible-playbook \
  -i inventories/production/hosts.yml \
  playbooks/change_password.yml \
  --ask-vault-pass
```

## Optional usage: HMAC salt from Vault secret

Use this only when the clear password is supplied securely from Ansible Vault, AWX credential/survey, HashiCorp Vault, CyberArk, or another secret manager.

```yaml
change_password_require_hash: false
change_password_allow_plaintext_password: true
change_password_hash_salt_mode: hmac_inventory
change_password_hmac_salt_secret: "use-a-long-random-secret-from-vault-minimum-24-chars"

change_password_accounts:
  - username: root
    password_plain: "Use-A-Vault-Secret-Value-2026!"
    expire: false
    state: present
```

Salt formula:

```text
salt = HMAC-SHA256(change_password_hmac_salt_secret, "prefix:username:inventory_hostname")[:16]
```

Benefits:

- same password produces different hashes per host and per user;
- salt is deterministic, so Ansible remains idempotent;
- salt is not publicly predictable without the Vault secret;
- `/etc/shadow` hash correlation across hosts is reduced.

## Multiple accounts

```yaml
change_password_accounts:
  - username: root
    password_hash: "$6$rounds=656000$..."
    expire: false

  - username: ansible
    password_hash: "$6$rounds=656000$..."
    expire: true
    state: unlocked

  - username: deploy
    password_hash: "$6$rounds=656000$..."
    state: locked
```

## Password ageing

```yaml
change_password_set_aging: true
change_password_min_days: 1
change_password_max_days: 90
change_password_warn_days: 14
change_password_inactive_days: 30
```

## Main variables

| Variable | Default | Description |
|---|---:|---|
| `change_password_accounts` | `[]` | Accounts to manage |
| `change_password_require_hash` | `true` | Require `password_hash` |
| `change_password_allow_plaintext_password` | `false` | Allow `password_plain` |
| `change_password_hash_salt_mode` | `hmac_inventory` | Salt mode for plaintext workflow |
| `change_password_hmac_salt_secret` | `""` | Secret key used by HMAC salt derivation |
| `change_password_hmac_algorithm` | `sha256` | HMAC digest algorithm |
| `change_password_hash_salt_prefix` | `chgpassword:v2` | Stable prefix included in HMAC message |
| `change_password_salt_length` | `16` | SHA512 crypt salt length, max 16 |
| `change_password_allow_public_deterministic_salt` | `false` | Permit legacy non-secret deterministic salt |
| `change_password_use_no_log` | `true` | Hide sensitive task output |
| `change_password_manage_root` | `true` | Allow root password rotation |
| `change_password_allow_root_lock` | `false` | Allow locking root |
| `change_password_fail_if_user_missing` | `true` | Fail if local user is absent |
| `change_password_audit_enabled` | `true` | Write audit event without secrets |
| `change_password_audit_file` | `/var/log/ansible/change-password.log` | Audit file path |

## FreeIPA / IdM / LDAP warning

This role changes local `/etc/shadow` passwords only. For FreeIPA, Red Hat IdM, LDAP, or Active Directory accounts, use the identity provider API/module instead.
