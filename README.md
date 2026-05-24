# IRIVEN ChangePassword

Enterprise-grade Ansible role for secure local UNIX password rotation and account hardening.

## Overview

IRIVEN ChangePassword is a hardened Ansible role designed for controlled password rotation workflows on Linux systems.  
The role focuses exclusively on existing local account password management and operational compliance.

The project is intentionally scoped to:
- Local account password rotation
- Account lock and unlock operations
- Password ageing enforcement
- Compliance-oriented hardening controls
- Secure CI/CD validation workflows

The role does not provision users, manage SSH keys, configure sudoers, or perform identity lifecycle management.

---

## Key Features

- Existing local accounts only
- SHA512 password hashing by default
- Optional SHA256 hash support
- Password ageing enforcement
- Secure HMAC-based internal protection workflow
- Strict validation and preflight controls
- Molecule integration tests
- Enterprise CI pipeline validation
- Idempotent execution model
- Hardened runtime behavior
- Secure defaults

---

## Supported Platforms

Validated on:
- Ubuntu 22.04+
- Debian 12+
- RHEL 8+
- Rocky Linux 8+
- AlmaLinux 8+

---

## Project Structure

```text
inventories/
└── production/
    └── group_vars/
        └── all/
            ├── main.yml
            └── vault.yml

roles/
└── changepassword/
    ├── defaults/
    ├── handlers/
    ├── meta/
    ├── molecule/
    ├── plugins/
    ├── tasks/
    │   └── tasks.d/
    ├── templates/
    └── vars/

.github/
└── workflows/
```

---

## Inventory Variables

### main.yml

```yaml
iriven_chgpasswd_hash_algorithm: sha512
iriven_chgpasswd_sha512_rounds: 656000

iriven_chgpasswd_set_aging: true
iriven_chgpasswd_min_days: 3
iriven_chgpasswd_max_days: 90
iriven_chgpasswd_warn_days: 14
iriven_chgpasswd_inactive_days: null

iriven_chgpasswd_use_no_log: true
```

---

### vault.yml

```yaml
# REQUIRED
# Replace with a strong custom secret.
# Minimum 32 characters with upper/lower/digit/special characters.
# Example:
# iriven_chgpasswd_hmac_salt_secret: "MyStrongSecret#2026!"

iriven_chgpasswd_hmac_salt_secret: ""

unix_local_accounts:
  - username: root
    password: "StrongPassword#2026!"

  - username: ansible
    password: "AnotherStrongPassword#2026!"
    state: unlocked
```

---

## Account Model

```yaml
unix_local_accounts:
  - username: root
    password: "StrongPassword#2026!"
    state: unlocked
    expire: false
```

### Supported Attributes

| Attribute | Required | Description |
|---|---|---|
| username | Yes | Existing local UNIX account |
| password | Yes | Plaintext or supported hash |
| state | No | locked / unlocked |
| expire | No | Force password change at next login |

---

## Runtime Targeting

Single account execution:

```bash
ansible-playbook playbooks/changepassword.yml -e TGT_USER=root
```

All declared accounts:

```bash
ansible-playbook playbooks/changepassword.yml -e TGT_USER=all
```

---

## Security Controls

- Strict account validation
- Existing account enforcement
- Shadow backend verification
- Login shell validation
- Password complexity validation
- HMAC secret validation
- Runtime secret cleanup
- Hardened Ansible configuration
- CI security gates
- Idempotence verification

---

## CI/CD Validation

The project includes:
- YAML validation
- ansible-lint production profile
- syntax-check validation
- Molecule functional testing
- idempotence testing
- Docker-based integration testing

---

## Molecule Validation

Molecule validates:
- Existing account handling
- Password rotation
- Lock and unlock behavior
- Password ageing
- Idempotence compliance

---

## Usage

```yaml
- name: Rotate local passwords
  hosts: linux
  become: true

  roles:
    - role: changepassword
```

---

## Operational Scope

This role intentionally excludes:
- User provisioning
- Group management
- SSH key management
- Home directory management
- Sudo policy management
- Identity lifecycle orchestration

---

## Authors

Alfred TCHONDJO  
Project Initiator — IRIVEN Group

---

## Copyright

© IRIVEN Group — All Rights Reserved
