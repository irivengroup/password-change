# Security notes

## Default model

The safest default is to provide a precomputed SHA512 crypt hash through Ansible Vault or another secret manager. In this mode, the role does not need to handle plaintext passwords.

## HMAC salt model

When plaintext input is explicitly enabled, this version does not use a public deterministic salt. It derives the crypt salt with a secret-backed HMAC:

```text
salt = HMAC-SHA256(secret, prefix:username:inventory_hostname)[:16]
```

This gives deterministic idempotence while preventing an attacker from recalculating salts only from usernames and hostnames.

## Security impact

Advantages:

- different hashes for the same password across users and hosts;
- no public salt derivation from inventory data alone;
- stable idempotence across Ansible runs;
- better resistance to cross-host hash correlation if `/etc/shadow` leaks;
- compatible with GitOps and AWX when secrets are injected securely.

Residual risks:

- if the plaintext password is weak, offline cracking is still possible after a shadow leak;
- if the HMAC secret leaks, salts become predictable again;
- if `inventory_hostname` changes, the derived hash changes;
- this is for local Linux accounts only, not FreeIPA/LDAP/AD identities.

## Operational recommendations

- Keep `change_password_require_hash: true` whenever possible.
- Store `change_password_hmac_salt_secret` only in Vault/AWX/secret-manager.
- Use a long random HMAC secret, at least 24 characters, preferably 32+ bytes.
- Rotate the HMAC secret carefully; rotation changes all derived hashes for plaintext workflow.
- Keep `change_password_use_no_log: true`.
- Avoid shared break-glass passwords where possible.
- Test root password changes on a maintenance window and keep an out-of-band recovery path.

## Legacy deterministic salt

The legacy mode based on `sha256(prefix:username:inventory_hostname)` is still present for backward compatibility but blocked by default. It requires:

```yaml
change_password_hash_salt_mode: deterministic_inventory
change_password_allow_public_deterministic_salt: true
```

Do not use it for production unless you explicitly accept public salt predictability.
