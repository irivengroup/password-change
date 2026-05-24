# IRIVEN ChangePassword

**IRIVEN ChangePassword** is an enterprise-grade Ansible role dedicated to controlled password rotation for existing local UNIX accounts.

The role is designed for production environments where password changes must be secure, auditable, idempotent, and governed by strict operational controls.

---

## Purpose

This project provides a hardened automation workflow for changing passwords on existing local Linux accounts, including privileged accounts such as `root`.

It is intentionally focused on password rotation and local account hardening. It does not create users, provision identities, manage sudo policies, deploy SSH keys, or perform lifecycle management.

---

## Key Capabilities

- Password rotation for existing local UNIX accounts
- Support for `root` and standard local users
- Targeted execution through `TGT_USER`
- Bulk execution for all declared accounts
- Required password declaration for every managed account
- SHA512 password hashing by default
- Support for pre-hashed SHA512 and SHA256 Linux-compatible password values
- Account lock and unlock handling
- Optional password expiration at next login
- Global password ageing policy enforcement
- Strict preflight validation before modification
- Local account backend validation
- Login shell validation
- `/etc/shadow` hardening checks
- Secure runtime handling with `no_log`
- Sensitive fact cleanup after execution
- CI/CD validation pipeline
- Molecule functional and idempotence tests

---

## Supported Platforms

The role targets modern Linux distributions using standard local UNIX account backends:

- Red Hat Enterprise Linux 8+
- Rocky Linux 8+
- AlmaLinux 8+
- Debian 12+
- Ubuntu 22.04+
- SUSE Linux Enterprise Server 15+
- openSUSE Leap 15.5+

---

### SUSE Compatibility Notes

SUSE targets are supported through the standard local UNIX account stack. Ensure the managed host provides:

- `/etc/passwd` and `/etc/shadow` local account backends
- `getent` for account discovery
- `/usr/bin/chage` for password ageing and expiration operations
- login shells such as `/bin/bash` or `/usr/bin/bash` for targeted interactive accounts

On SLES/openSUSE systems, `chage` is typically provided by the `shadow` package.

---

## Project Layout

```text
.
├── ansible.cfg
├── inventories/
│   └── production/
│       ├── hosts.yml
│       └── group_vars/
│           └── all/
│               ├── main.yml
│               └── vault.yml
├── playbooks/
│   └── change_password.yml
├── requirements.txt
├── requirements.yml
├── roles/
│   └── changepassword/
│       ├── defaults/
│       ├── meta/
│       ├── molecule/
│       ├── plugins/
│       └── tasks/
│           ├── main.yml
│           └── tasks.d/
│               ├── aging.yml
│               ├── apply.yml
│               ├── audit.yml
│               ├── normalize.yml
│               ├── preflight.yml
│               └── shadow.yml
└── .github/
    └── workflows/
        └── ci.yml
```

---

## Inventory Model

The production inventory uses a split configuration model:

```text
inventories/
└── production/
    └── group_vars/
        └── all/
            ├── main.yml
            └── vault.yml
```

`main.yml` contains non-sensitive operational defaults.  
`vault.yml` contains sensitive account and password data and must be encrypted with Ansible Vault.

---

## Global Configuration

Example `inventories/production/group_vars/all/main.yml`:

```yaml
---
TGT_USER: root

iriven_chgpasswd_hash_algorithm: sha512
iriven_chgpasswd_require_hash: false
iriven_chgpasswd_allow_plaintext_password: true
iriven_chgpasswd_default_hash_rounds: 656000
iriven_chgpasswd_min_hash_rounds: 500000
iriven_chgpasswd_min_hmac_secret_length: 32

iriven_chgpasswd_use_no_log: true
iriven_chgpasswd_fail_if_user_missing: true
iriven_chgpasswd_manage_root: true
iriven_chgpasswd_allow_root_lock: false
iriven_chgpasswd_allow_empty_password: false

iriven_chgpasswd_require_login_shell: true
iriven_chgpasswd_require_etc_passwd_user: true
iriven_chgpasswd_fail_if_same_hash: false

iriven_chgpasswd_set_aging: false
iriven_chgpasswd_min_days: null
iriven_chgpasswd_max_days: null
iriven_chgpasswd_warn_days: null
iriven_chgpasswd_inactive_days: null
```

---

## Python Password Hash Generation

The role accepts Linux-compatible SHA512 and SHA256 password hashes. SHA512 is recommended for production use.

Generate a SHA512 crypt hash with Python:

```bash
python3 -c 'import crypt,getpass; print(crypt.crypt(getpass.getpass("Password: "), crypt.mksalt(crypt.METHOD_SHA512)))'
```

Generate a SHA256 crypt hash with Python:

```bash
python3 -c 'import crypt,getpass; print(crypt.crypt(getpass.getpass("Password: "), crypt.mksalt(crypt.METHOD_SHA256)))'
```

Alternative using `passlib`:

```bash
python3 -c 'from passlib.hash import sha512_crypt; import getpass; print(sha512_crypt.hash(getpass.getpass("Password: ")))'
```

Accepted hash prefixes:

- `$6$` for SHA512 crypt
- `$5$` for SHA256 crypt

Store generated hashes only in Vault-protected inventory files and never commit real credentials in clear text.


## Vault Configuration

Example `inventories/production/group_vars/all/vault.yml`:

```yaml
---
# REQUIRED
# Replace this value with a strong custom HMAC salt secret.
# Minimum: 32 characters.
# Complexity: at least one uppercase letter, one lowercase letter, one digit,
# and one special character.
iriven_chgpasswd_hmac_salt_secret: ""

unix_local_accounts:
  - username: root
    password: "replace-with-vault-secret-root-password"

  - username: ansible
    password: "replace-with-vault-secret-ansible-password"
    state: unlocked

  - username: svc_backup
    password: "$6$rounds=656000$replaceSaltHere$replaceSha512CryptHashHere"
    state: locked
    expire: false
```

Encrypt the file before committing or using it in production:

```bash
ansible-vault encrypt inventories/production/group_vars/all/vault.yml
```

---

## Account Declaration

`unix_local_accounts` is a list of account declarations.

Each item must represent an account that already exists locally on the managed host.

```yaml
unix_local_accounts:
  - username: root
    password: "StrongPassword#2026!"
    state: unlocked
    expire: false
```

### Supported Account Fields

| Field | Required | Values | Description |
|---|---:|---|---|
| `username` | Yes | local UNIX username | Account to manage |
| `password` | Yes | plaintext or Linux password hash | New password material |
| `state` | No | `locked`, `unlocked` | Password lock state |
| `expire` | No | `true`, `false` | Force password change at next login |

Unsupported provisioning attributes are intentionally rejected.

---

## Password Handling

Every account declaration must include `password`.

Accepted password formats:

- Plaintext value stored inside encrypted `vault.yml`
- SHA512 crypt hash beginning with `$6$`
- SHA256 crypt hash beginning with `$5$`

Plaintext values are processed by the role and converted into Linux-compatible password hashes. SHA512 is used by default for generated hashes.

Recommended production posture:

```yaml
iriven_chgpasswd_hash_algorithm: sha512
iriven_chgpasswd_default_hash_rounds: 656000
iriven_chgpasswd_min_hash_rounds: 500000
```

---

## Execution Examples with Vault

All production executions should use Ansible Vault because `vault.yml` contains sensitive password material.

The examples below use the production inventory:

```text
inventories/production/hosts.yml
```

and the playbook:

```text
playbooks/change_password.yml
```

### Without `TGT_USER`

When `TGT_USER` is not passed as an extra variable, the role uses the default value defined by the project configuration. The default target is `root`.

```bash
ansible-playbook \
  -i inventories/production/hosts.yml \
  playbooks/change_password.yml \
  --ask-vault-pass
```

With a Vault password file:

```bash
ansible-playbook \
  -i inventories/production/hosts.yml \
  playbooks/change_password.yml \
  --vault-password-file ~/.vault_pass.txt
```

### With `TGT_USER=root`

Use this mode to rotate only the `root` password, provided `root` is declared in `unix_local_accounts`.

```bash
ansible-playbook \
  -i inventories/production/hosts.yml \
  playbooks/change_password.yml \
  --ask-vault-pass \
  -e TGT_USER=root
```

### With `TGT_USER=<user>`

Use this mode to rotate only one declared local account. Replace `<user>` with a username present in `unix_local_accounts`.

```bash
ansible-playbook \
  -i inventories/production/hosts.yml \
  playbooks/change_password.yml \
  --ask-vault-pass \
  -e TGT_USER=ansible
```

### With `TGT_USER=all`

Use this mode to rotate all declared accounts.

```bash
ansible-playbook \
  -i inventories/production/hosts.yml \
  playbooks/change_password.yml \
  --ask-vault-pass \
  -e TGT_USER=all
```

### With `TGT_USER='*'`

The wildcard target is also supported for rotating all declared accounts. Quote the value to prevent shell expansion.

```bash
ansible-playbook \
  -i inventories/production/hosts.yml \
  playbooks/change_password.yml \
  --ask-vault-pass \
  -e 'TGT_USER=*'
```

The role fails when `TGT_USER` references an account that is not declared in `unix_local_accounts`.

---

## Operational Workflows

Before executing the playbook in production, perform the following operational checks.

### 1. Confirm Local Account Presence

Ensure every account declared in `unix_local_accounts` already exists locally on all targeted hosts.

This role does not create users.

### 2. Prepare Vault Data

Populate `inventories/production/group_vars/all/vault.yml` with:

- `iriven_chgpasswd_hmac_salt_secret`
- `unix_local_accounts`
- one `password` value per account

Then encrypt the file:

```bash
ansible-vault encrypt inventories/production/group_vars/all/vault.yml
```

### 3. Validate Inventory Targeting

Review the inventory and confirm the execution scope:

```bash
ansible-inventory \
  -i inventories/production/hosts.yml \
  --list
```

### 4. Run Static Validation

Run syntax validation before production execution:

```bash
ansible-playbook \
  -i inventories/production/hosts.yml \
  playbooks/change_password.yml \
  --syntax-check
```

### 5. Run CI or Molecule Before Rollout

Run the same validation chain used by the repository CI:

```bash
yamllint .
ansible-lint --profile production
molecule test
```

### 6. Execute with Explicit Scope

Use the `Execution Examples with Vault` section as the single command reference for all supported execution modes.

### 7. Use Vault Password File When Required

For controlled automation environments, prefer a protected Vault password file and restrict its permissions:

```bash
chmod 600 ~/.vault_pass.txt
```

### 8. Review Audit Output

When audit logging is enabled, review the managed-host audit file after execution:

```text
/var/log/ansible/changepassword.log
```

Audit entries must never contain plaintext passwords, generated hashes, or secret material.

---

## Playbook

Example `playbooks/change_password.yml`:

```yaml
---
- name: Change local UNIX account passwords
  hosts: all
  become: true

  roles:
    - role: changepassword
```

Execution commands are consolidated in the `Execution Examples with Vault` section.

---

## Security Controls

The role enforces multiple controls before applying password changes:

- account declaration validation
- duplicate username detection
- mandatory password presence
- forbidden account protection
- local account existence checks
- local backend checks
- login shell allow-list validation
- shadow file availability and permission checks
- password complexity checks for plaintext values
- hash format validation for pre-hashed values
- root lock protection
- controlled account lock/unlock behavior
- sensitive runtime fact cleanup

---

## Password Ageing Policy

Password ageing is configured globally:

```yaml
iriven_chgpasswd_set_aging: false
iriven_chgpasswd_min_days: null
iriven_chgpasswd_max_days: null
iriven_chgpasswd_warn_days: null
iriven_chgpasswd_inactive_days: null
```

Aging is disabled by default. Set these values explicitly in inventory when a password ageing policy must be enforced.

---

## CI/CD Validation

The GitHub Actions pipeline validates:

- YAML parsing
- `yamllint`
- Python filter plugin syntax
- Ansible inventory parsing
- playbook syntax-check
- `ansible-lint` production profile
- project invariants
- Molecule functional tests
- Molecule idempotence tests

---

## Molecule Tests

The Molecule scenario validates the role against existing local accounts and checks:

- password rotation execution
- lock and unlock behavior
- password ageing policy application
- idempotence
- verification after converge

Molecule test users are created only by the test preparation phase. The role itself remains restricted to existing accounts.

---

## Automation Platform Guidance

For AWX or Ansible Automation Platform:

- store Vault credentials in managed credentials
- avoid plaintext password surveys
- restrict job template execution with RBAC
- require approval for `TGT_USER=all`
- use separate inventories per environment
- run validation jobs before production execution
- preserve job artifacts for audit review

---

## Compliance Notes

This role is suitable for controlled environments requiring:

- password rotation governance
- privileged account control
- audit-friendly execution
- repeatable automation
- CI/CD enforcement
- separation between password operations and identity provisioning

---


## Production Strict Controls

The role is designed for production-strict execution by default.

The following controls are mandatory:
- a custom HMAC salt secret must be provided through Vault;
- runtime `no_log` protection must remain enabled;
- audit logging must remain enabled;
- runtime locking must remain enabled;
- SHA512 rounds must respect the configured minimum.

No profile variable is required. Production strict behavior is the baseline.

## Test Coverage

The project includes functional and negative Molecule scenarios.

Functional validation covers:
- password rotation on existing local users;
- lock and unlock behavior;
- password ageing behavior;
- idempotence.

Negative validation covers:
- missing password;
- invalid account state;
- weak HMAC secret;
- missing local account.

Multi-distribution validation is available for:
- Ubuntu;
- Debian;
- Rocky Linux;
- openSUSE Leap.

## Authors

Alfred TCHONDJO  
Project Initiator — IRIVEN Group

---

## Copyright

© IRIVEN Group — All Rights Reserved
