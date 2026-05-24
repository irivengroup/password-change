# -*- coding: utf-8 -*-
"""
Ansible filter plugins for changepassword.

Provides deterministic, secret-backed HMAC salt derivation for SHA512 crypt.
The returned value is restricted to lowercase hex characters, which are valid
crypt(3) salt characters, and truncated by the role to the SHA512 crypt max
salt length of 16 characters.
"""

from __future__ import annotations

import hashlib
import hmac
from typing import Any


class FilterModule(object):
    """Custom filters used by the changepassword role."""

    def filters(self) -> dict[str, Any]:
        return {
            "iriven_chgpasswd_hmac_salt": self.iriven_chgpasswd_hmac_salt,
        }

    @staticmethod
    def iriven_chgpasswd_hmac_salt(message: Any, secret: Any, algorithm: str = "sha256", length: int = 16) -> str:
        """Return a deterministic HMAC digest fragment suitable for crypt salt.

        Args:
            message: Stable public message, usually prefix:username:inventory_hostname.
            secret: Secret key from Ansible Vault/AWX/secret-manager.
            algorithm: hashlib algorithm name. sha256 or sha512 recommended.
            length: returned salt length. SHA512 crypt accepts max 16.
        """
        if secret is None or str(secret) == "":
            raise AnsibleFilterError("iriven_chgpasswd_hmac_salt requires a non-empty secret")

        if int(length) < 8 or int(length) > 16:
            raise AnsibleFilterError("iriven_chgpasswd_hmac_salt length must be between 8 and 16")

        normalized_algorithm = str(algorithm).lower()
        if normalized_algorithm not in hashlib.algorithms_available:
            raise AnsibleFilterError(f"Unsupported digest algorithm: {algorithm}")

        digestmod = getattr(hashlib, normalized_algorithm, None)
        if digestmod is None:
            raise AnsibleFilterError(f"Unsupported hashlib constructor: {algorithm}")

        raw = hmac.new(
            key=str(secret).encode("utf-8"),
            msg=str(message).encode("utf-8"),
            digestmod=digestmod,
        ).hexdigest()

        return raw[: int(length)]


try:
    from ansible.errors import AnsibleFilterError
except Exception:  # pragma: no cover
    class AnsibleFilterError(Exception):
        pass
