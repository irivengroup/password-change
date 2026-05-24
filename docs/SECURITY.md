# Security notes

`vault.yml` is expected to be fully encrypted with Ansible Vault or supplied by AWX/AAP credentials.

The preferred account model is:

```yaml
unix_local_accounts:
  - username: root
    password: "VaultProtectedPasswordOrSha512Hash"
```

`password` is auto-detected:

- `$6$...` is accepted as SHA512 crypt;
- `$5$...` is accepted as SHA256 crypt;
- any other value is treated as plaintext from Vault and hashed using SHA512 crypt.

Defaults are intentionally minimal in Vault:

```yaml
manage_password: true
expire: false
# state omitted => lock state unchanged
```

Hardening rules:

- only `password` may be declared; legacy keys `password` and `password` are rejected;
- per-account `aging:` is rejected; use global `iriven_chgpasswd_*` variables;
- user creation is intentionally unsupported; the account must already exist locally;
- provisioning attributes such as `shell`, `groups`, `append`, `uid`, `group`, `home`, `comment`, `create_home` and `system` are rejected;
- forbidden system accounts are rejected;
- root locking is blocked unless explicitly enabled;
- local `/etc/passwd` and `/etc/shadow` checks reduce the risk of mutating LDAP/IPA/AD accounts locally;
- HMAC salt derivation uses `machine-id` by default;
- secret values and hashes are hidden with `no_log`.
