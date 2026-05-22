# Ansible Chgpassword 

Ansible playbook and role to change a local Linux user password, including `root`.

## Features

- Supports `root` and standard local Linux users
- Supports one or many accounts
- Accepts precomputed SHA512 hashes or clear passwords from Vault/CI secrets
- Uses `no_log` by default for sensitive tasks
- Optional password expiry at next login
- Optional account lock/unlock
- Safe validation before applying changes
- Compatible with RHEL, Rocky Linux, AlmaLinux, Debian, and Ubuntu

## Project layout

```text
.
├── ansible.cfg
├── inventories/production/hosts.yml
├── inventories/production/group_vars/all.yml
├── playbooks/change_password.yml
├── requirements.yml
└── roles/ChangePassword
```

## Recommended usage with password hash

Generate a SHA512 hash:

```bash
python3 - <<'PY'
import crypt
import getpass
password = getpass.getpass('Password: ')
print(crypt.crypt(password, crypt.mksalt(crypt.METHOD_SHA512)))
PY
```

Then define:

```yaml
change_password_accounts:
  - username: root
    password_hash: "$6$rounds=656000$example$replace_with_real_hash"
    expire: false
```

Encrypt the variable file:

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

## Usage with clear password

Only use this through Ansible Vault, AWX Survey, GitLab CI masked variables, or another secret manager.

```yaml
change_password_accounts:
  - username: root
    password_plain: "StrongPassword2026!"
    expire: false
```

## Multiple users

```yaml
change_password_accounts:
  - username: root
    password_hash: "$6$rounds=656000$..."
    expire: false

  - username: ansible
    password_plain: "AnotherStrongPassword2026!"
    expire: true

  - username: deploy
    password_plain: "DeployStrongPassword2026!"
    state: unlocked
```

## Important variables

| Variable | Default | Description |
|---|---:|---|
| `change_password_accounts` | `[]` | List of accounts to update |
| `change_password_default_hash_rounds` | `656000` | SHA512 rounds when hashing clear password |
| `change_password_enforce_complexity` | `true` | Enforce basic complexity for clear passwords |
| `change_password_min_length` | `14` | Minimum length for clear passwords |
| `change_password_fail_if_user_missing` | `true` | Fail if target local user does not exist |
| `change_password_use_no_log` | `true` | Hide secrets from Ansible logs |

## Notes for root password change

Use a sudo-capable SSH account:

```yaml
ansible_user: ansible
ansible_become: true
```

The role can update `root` even when direct root SSH is disabled, provided privilege escalation works.

## FreeIPA / Red Hat IdM warning

This role changes local Linux passwords via `/etc/shadow`. For centralized users managed by FreeIPA, Red Hat IdM, LDAP, or Active Directory, use the identity backend instead of this role.

For FreeIPA, prefer `community.general.ipa_user`.

## Security recommendations

- Never commit clear passwords.
- Prefer `password_hash` over `password_plain`.
- Keep `change_password_use_no_log: true`.
- Use Ansible Vault, AWX credentials, HashiCorp Vault, CyberArk, or CI masked variables.
- Test on a non-critical host before production rollout.
