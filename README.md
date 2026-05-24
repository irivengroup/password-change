# IRIVEN Change Password

**IRIVEN Change Password** is an enterprise-oriented Ansible role for controlled password rotation and account password-state hardening on existing Unix/Linux local accounts.

The role is intentionally scoped to password compliance only. It does not create users, remove users, provision groups, manage home directories, deploy SSH keys, or alter shell/profile ownership. Those responsibilities must remain in a dedicated identity or Unix account lifecycle role.

## Purpose

This project provides a secure, auditable, and repeatable mechanism to rotate passwords for existing local Unix accounts, including `root`, across one or many managed hosts.

It is designed for environments where password rotation must be:

- deterministic and idempotent;
- compatible with Ansible Vault, AWX, AAP, and CI/CD workflows;
- safe for privileged accounts such as `root`;
- explicit about target selection through `TGT_USER`;
- resistant to accidental user creation;
- suitable for security audit and operational governance.

## Key Capabilities

- Rotate passwords for existing local users only.
- Support `root` password rotation.
- Target a single declared account with `TGT_USER`.
- Rotate all declared accounts with `TGT_USER=all`.
- Store account definitions in a Vault-protected inventory file.
- Use a single `password` field per account.
- Automatically detect SHA512 crypt hashes starting with `$6$`.
- Automatically detect SHA256 crypt hashes starting with `$5$`.
- Generate SHA512 crypt hashes by default for plaintext Vault-protected passwords.
- Derive deterministic salts from `username + machine-id` using an HMAC secret.
- Apply global password ageing policy.
- Lock or unlock account password state when requested.
- Prevent unsupported legacy fields such as `password_hash` and `password_plain`.
- Use `ansible.builtin.getent` for account discovery where possible.
- Keep task logic split under `tasks.d/` for maintainability.

## Non-Goals

This role deliberately does not manage:

- user creation;
- user deletion;
- UID/GID assignment;
- primary or secondary groups;
- home directories;
- SSH authorized keys;
- sudoers policy;
- login shell provisioning;
- LDAP, FreeIPA, SSSD, or centralized identity password changes.

If a declared account does not already exist locally on the target host, the role fails fast.

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
│               ├── vault.yml
│               └── vault.yml.example
├── playbooks/
│   └── change_password.yml
├── roles/
│   └── changepassword/
│       ├── defaults/
│       │   └── main.yml
│       ├── filter_plugins/
│       │   └── crypto_salt.py
│       ├── meta/
│       │   └── main.yml
│       └── tasks/
│           ├── main.yml
│           └── tasks.d/
│               ├── aging.yml
│               ├── apply.yml
│               ├── audit.yml
│               ├── normalize.yml
│               ├── preflight.yml
│               └── shadow.yml
└── docs/
    └── SECURITY.md
```

## Inventory Design

The inventory uses a split `group_vars/all` layout:

```text
inventories/production/group_vars/all/
├── main.yml
└── vault.yml
```

`main.yml` contains non-secret global policy settings.

`vault.yml` contains sensitive data and must be encrypted with Ansible Vault.

## Global Configuration

Example `inventories/production/group_vars/all/main.yml`:

```yaml
---
iriven_chgpasswd_hash_algorithm: sha512
iriven_chgpasswd_sha512_rounds: 656000

iriven_chgpasswd_set_aging: true
iriven_chgpasswd_min_days: 3
iriven_chgpasswd_max_days: 90
iriven_chgpasswd_warn_days: 14
iriven_chgpasswd_inactive_days: null

iriven_chgpasswd_manage_password_default: true
```

### Password Ageing Defaults

The recommended enterprise baseline is:

```yaml
iriven_chgpasswd_set_aging: true
iriven_chgpasswd_min_days: 3
iriven_chgpasswd_max_days: 90
iriven_chgpasswd_warn_days: 14
iriven_chgpasswd_inactive_days: null
```

This means:

- the password cannot be changed again before 3 days;
- the password expires after 90 days;
- the user is warned 14 days before expiration;
- the account is not automatically disabled after expiration.

## Vault Configuration

Example `inventories/production/group_vars/all/vault.yml` before encryption:

```yaml
---
unix_local_accounts:
  - username: root
    password: "ReplaceWithRootPassword"

  - username: ansible
    password: "ReplaceWithAnsiblePassword"
    state: unlocked
    expire: false

  - username: svc_backup
    password: "$6$rounds=656000$existingSalt$existingHash"
    state: locked

iriven_chgpasswd_hmac_secret: "ReplaceWithStrongHmacSecret"
```

Encrypt the file:

```bash
ansible-vault encrypt inventories/production/group_vars/all/vault.yml
```

Edit it later with:

```bash
ansible-vault edit inventories/production/group_vars/all/vault.yml
```

## Account Schema

`unix_local_accounts` is a list of dictionaries.

Supported account properties:

| Property | Required | Description |
|---|---:|---|
| `username` | yes | Existing local account name. |
| `password` | no | Plaintext Vault-protected password or existing SHA256/SHA512 crypt hash. |
| `state` | no | Password lock state. Allowed values: `locked`, `unlocked`. If omitted, lock state is unchanged. |
| `expire` | no | Boolean. If `true`, force password change at next login. |
| `manage_password` | no | Boolean. Defaults to `true`. If `false`, password value is not changed. |

Unsupported legacy fields are rejected:

```yaml
password_hash: "..."
password_plain: "..."
```

Provisioning fields are also rejected because this role does not create or manage user lifecycle attributes.

## Password Hash Detection

The `password` field supports three modes:

### Plaintext Password

```yaml
password: "MyStrongPassword"
```

The role generates a SHA512 crypt hash using the configured rounds and deterministic HMAC-derived salt.

### SHA512 Crypt Hash

```yaml
password: "$6$rounds=656000$salt$hash"
```

The hash is used as provided.

### SHA256 Crypt Hash

```yaml
password: "$5$rounds=656000$salt$hash"
```

The hash is used as provided.

SHA512 remains the default generation algorithm.

## Salt Derivation

For plaintext Vault-protected passwords, the generated salt is derived from:

```text
username + machine-id
```

The derivation uses an HMAC secret stored in Vault:

```yaml
iriven_chgpasswd_hmac_secret: "ReplaceWithStrongHmacSecret"
```

This design provides:

- stable idempotence across repeated runs;
- a different hash per user and per machine;
- no dependency on mutable inventory hostnames;
- no random salt drift at every execution;
- reduced correlation between identical passwords on different hosts.

The role requires a valid machine-id from the target host. It does not use `inventory_hostname` as a salt fallback.

## Target Selection with TGT_USER

`TGT_USER` controls which declared account is processed.

Default behavior:

```bash
-e TGT_USER=root
```

Rotate only `root`:

```bash
ansible-playbook -i inventories/production/hosts.yml playbooks/change_password.yml \
  -e TGT_USER=root \
  --ask-vault-pass
```

Rotate only `ansible`:

```bash
ansible-playbook -i inventories/production/hosts.yml playbooks/change_password.yml \
  -e TGT_USER=ansible \
  --ask-vault-pass
```

Rotate all declared accounts:

```bash
ansible-playbook -i inventories/production/hosts.yml playbooks/change_password.yml \
  -e TGT_USER=all \
  --ask-vault-pass
```

If `TGT_USER` references an account not declared in `unix_local_accounts`, the role fails.

## Execution

Run against the production inventory:

```bash
ansible-playbook -i inventories/production/hosts.yml playbooks/change_password.yml --ask-vault-pass
```

With a specific target account:

```bash
ansible-playbook -i inventories/production/hosts.yml playbooks/change_password.yml \
  -e TGT_USER=root \
  --ask-vault-pass
```

With an external Vault password file:

```bash
ansible-playbook -i inventories/production/hosts.yml playbooks/change_password.yml \
  -e TGT_USER=all \
  --vault-password-file .vault-pass
```

## AWX / Ansible Automation Platform Usage

Recommended survey variable:

```text
TGT_USER
```

Allowed operational values:

- `root`
- any declared username from `unix_local_accounts`
- `all`

Recommended AWX configuration:

- store Vault credentials in AWX credentials;
- restrict `TGT_USER=all` to privileged operators;
- enable job isolation and approval workflows for production;
- retain job event logs but never expose secrets;
- use separate inventories for production, staging, and lab environments.

## Security Model

The role is designed around the following principles:

- secrets are stored in Ansible Vault;
- account lists are explicit and controlled;
- users are never created implicitly;
- unsupported account lifecycle attributes are rejected;
- password hashes are hidden from logs where practical;
- HMAC salt derivation avoids host-name based drift;
- SHA512 crypt is the default hash generation algorithm;
- SHA256 and SHA512 crypt hashes are supported for pass-through compatibility;
- password ageing is globally controlled and auditable.

## Operational Safety

Before applying password changes, the role validates that:

- `unix_local_accounts` is a list of dictionaries;
- each account has a unique `username`;
- `TGT_USER` is either `all` or a declared username;
- the target user exists locally;
- legacy password fields are not used;
- unsupported provisioning attributes are not present;
- the target account is not an LDAP/IPA-only account;
- machine-id is available for plaintext password hashing.

## Recommended Workflow

1. Update `vault.yml` with the intended account password values.
2. Encrypt or edit the file with Ansible Vault.
3. Run first against a limited host group.
4. Rotate a single account with `TGT_USER=<username>`.
5. Validate login and sudo paths.
6. Expand gradually to larger host groups.
7. Use `TGT_USER=all` only for controlled bulk rotation windows.

## Validation

Run YAML validation:

```bash
yamllint .
```

Run Ansible linting:

```bash
ansible-lint
```

Run a syntax check:

```bash
ansible-playbook -i inventories/production/hosts.yml playbooks/change_password.yml --syntax-check
```

## Compliance Notes

This project supports common enterprise password governance requirements:

- defined password maximum age;
- password minimum age;
- password expiry warning window;
- controlled privileged account rotation;
- auditable declared account scope;
- no implicit account creation;
- deterministic password hashing;
- Vault-based secret handling.

Security policy must still define password complexity, break-glass access, emergency rollback, privileged access management, and operator authorization.

## Limitations

- This role is for local Unix/Linux accounts only.
- It does not change passwords in FreeIPA, LDAP, Active Directory, or SSSD identity providers.
- It does not create missing users.
- It does not manage SSH keys or sudo policy.
- It does not guarantee password complexity unless enforced externally or by PAM policy.
- It assumes the target host exposes a stable machine-id.

## Release Governance

The README is considered the authoritative functional documentation for the project baseline. Future modifications should be intentional, reviewed, and aligned with the role scope.

## Authors

Alfred TCHONDJO  
Project Initiator — IRIVEN Group

## Copyright

© IRIVEN Group — All Rights Reserved
