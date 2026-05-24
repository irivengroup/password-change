# IRIVEN ChangePassword

Enterprise-grade Ansible role for secure local UNIX password rotation and account hardening.

## Operational Workflows

Before executing the playbook in production environments:

1. Ensure all target accounts already exist locally on managed hosts.
2. Populate `inventories/production/group_vars/all/vault.yml`.
3. Define a strong `iriven_chgpasswd_hmac_salt_secret`.
4. Encrypt sensitive inventory files using Ansible Vault.
5. Validate inventory targeting before execution.
6. Execute CI and Molecule validation workflows before production rollout.
7. Use `TGT_USER` to scope password rotation operations.
8. Run playbooks with privileged escalation (`become: true`).
9. Perform backup or snapshot operations before large-scale password rotation campaigns.

## Vault Usage Example

Encrypt the Vault file:

```bash
ansible-vault encrypt inventories/production/group_vars/all/vault.yml
```

Run using interactive Vault password prompt:

```bash
ansible-playbook playbooks/changepassword.yml   -i inventories/production/hosts.yml   --ask-vault-pass   -e TGT_USER=all
```

Run using a Vault password file:

```bash
ansible-playbook playbooks/changepassword.yml   -i inventories/production/hosts.yml   --vault-password-file ~/.vault_pass.txt   -e TGT_USER=root
```

## Authors

Alfred TCHONDJO
Project Initiator — IRIVEN Group

## Copyright

© IRIVEN Group — All Rights Reserved
