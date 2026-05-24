# changepassword Ansible

Hardened Ansible role and playbook to rotate and harden **existing local Linux account passwords**, including `root`. It does not create users or manage account provisioning attributes.

## Architecture

```text
inventories/
└── production/
    └── group_vars/
        └── all/
            ├── main.yml    # non-sensitive defaults
            └── vault.yml   # fully encrypted secrets

roles/changepassword/tasks/
├── main.yml
└── tasks.d/
    ├── preflight.yml
    ├── normalize.yml
    ├── shadow_precheck.yml
    ├── apply_password.yml
    ├── aging.yml
    └── audit.yml
```

## Vault model

`unix_local_accounts` is a **list of dictionaries** in `vault.yml`.

Preferred model:

```yaml
unix_local_accounts:
  - username: root
    password: "RootPasswordFromVault"

  - username: ansible
    password: "StrongPasswordFromVault"
    state: unlocked

  - username: svc_backup
    password: "$6$rounds=656000$replaceSalt$replaceSha512CryptHash"
    state: locked
    expire: false

  - username: legacy_sha256
    password: "$5$rounds=656000$replaceSalt$replaceSha256CryptHash"
    state: unlocked
```

Defaults per account:

```yaml
manage_password: true
expire: false
# state omitted => lock state unchanged
```

`manage_password` does **not** need to be repeated in `vault.yml` unless you want to override it.

This role is not a user lifecycle/provisioning role. It rejects account provisioning keys such as `shell`, `groups`, `append`, `uid`, `group`, `home`, `comment`, `create_home` and `system`. The account must already exist locally.

The `password` field is auto-detected:

- starts with `$6$` → treated as an existing SHA512 crypt hash and passed through;
- starts with `$5$` → treated as an existing SHA256 crypt hash and passed through;
- otherwise → treated as Vault-protected plaintext and hashed by the role using SHA512 crypt.

Only the `password` key is accepted. Legacy keys `password_hash` and `password_plain` are explicitly rejected.

## Runtime targeting

Default target is `root`:

```bash
ansible-playbook -i inventories/production/hosts.yml playbooks/change_password.yml --ask-vault-pass
```

Target one declared account:

```bash
ansible-playbook -i inventories/production/hosts.yml playbooks/change_password.yml --ask-vault-pass -e TGT_USER=ansible
```

Target all declared accounts:

```bash
ansible-playbook -i inventories/production/hosts.yml playbooks/change_password.yml --ask-vault-pass -e TGT_USER=all
```

The role refuses any `TGT_USER` not declared in `unix_local_accounts`.

## Hashing

Default hash algorithm:

```yaml
iriven_chgpasswd_hash_algorithm: sha512
iriven_chgpasswd_default_hash_rounds: 656000
```

For plaintext values stored inside the encrypted `vault.yml`, the final hash is generated with:

```text
salt = HMAC-SHA256(secret, prefix:username:machine-id)[:16]
hash = SHA512-crypt(password, salt, rounds)
```

This keeps idempotence stable and avoids equal hashes for equal passwords across different users or machines.

## Password ageing

Aging is global, not per account:

```yaml
iriven_chgpasswd_set_aging: true
iriven_chgpasswd_min_days: 3
iriven_chgpasswd_max_days: 90
iriven_chgpasswd_warn_days: 14
iriven_chgpasswd_inactive_days: null
```

Do not define `aging:` inside `unix_local_accounts`; the role rejects it.

## Main variables

| Variable | Default | Description |
|---|---:|---|
| `unix_local_accounts` | `[]` | Vault-declared local accounts |
| `TGT_USER` | `root` | Runtime selector: user or `all` |
| `iriven_chgpasswd_default_manage_password` | `true` | Default account password management |
| `iriven_chgpasswd_hash_algorithm` | `sha512` | Linux password hash algorithm |
| `iriven_chgpasswd_default_hash_rounds` | `656000` | SHA512 crypt rounds |
| `iriven_chgpasswd_hmac_salt_secret` | `""` | Vault secret used for HMAC salt derivation |
| `iriven_chgpasswd_hash_salt_mode` | `hmac_machine_id` | Salt derivation mode: HMAC secret + username + machine-id |
| `iriven_chgpasswd_use_no_log` | `true` | Hide sensitive task output |
| `iriven_chgpasswd_manage_root` | `true` | Allow root password management |
| `iriven_chgpasswd_allow_root_lock` | `false` | Block accidental root lock |

## Security guards

- full `vault.yml` encryption expected;
- one password source only per account;
- duplicate usernames rejected;
- missing users rejected before password mutation;
- provisioning attributes rejected;
- system/service accounts blocked by default;
- LDAP/IPA/AD/SSSD-only users rejected for local password mutation;
- generated salts are derived only from `username + machine-id`; no `inventory_hostname` fallback is supported;
- login shell validation enabled;
- `root` lock blocked unless explicitly allowed;
- sensitive tasks run with `no_log`;
- audit log contains no secret material.

## Builtin-first implementation

The role prioritizes builtin modules:

- `ansible.builtin.getent` for local account discovery;
- `ansible.builtin.user` for password and lock state;
- `ansible.builtin.stat` and `ansible.builtin.slurp` for local backend checks;
- `ansible.builtin.command` only for `chage`, because Ansible core has no dedicated password-aging module.
