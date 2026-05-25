# -*- coding: utf-8 -*-
"""
Ansible filter plugins for changepassword.

Provides deterministic, secret-backed HMAC salt derivation for SHA256/SHA512
Linux crypt password hashes. The returned value uses lowercase hexadecimal
characters only and is truncated by the role to the configured salt length.

Compatibility note:
This file intentionally avoids Python 3.7+ only syntax so it can be parsed on
older enterprise control nodes. The supported execution baseline remains driven
by the installed ansible-core version.
"""

import hashlib
import hmac

try:
    from ansible.errors import AnsibleFilterError
except Exception:  # pragma: no cover
    class AnsibleFilterError(Exception):
        pass

class FilterModule(object):
    """Custom filters used by the changepassword role."""

    def filters(self):
        return {
            "changepassword_hmac_salt": self.changepassword_hmac_salt,
        }

    @staticmethod
    def changepassword_hmac_salt(message, secret, algorithm="sha256", length=16):
        """Return a deterministic HMAC digest fragment suitable for crypt salt."""
        if secret is None or str(secret) == "":
            raise AnsibleFilterError("changepassword_hmac_salt requires a non-empty secret")

        try:
            salt_length = int(length)
        except (TypeError, ValueError):
            raise AnsibleFilterError("changepassword_hmac_salt length must be an integer")

        if salt_length < 8 or salt_length > 16:
            raise AnsibleFilterError("changepassword_hmac_salt length must be between 8 and 16")

        normalized_algorithm = str(algorithm).lower()
        if normalized_algorithm not in hashlib.algorithms_available:
            raise AnsibleFilterError("Unsupported digest algorithm: {0}".format(algorithm))

        digestmod = getattr(hashlib, normalized_algorithm, None)
        if digestmod is None:
            raise AnsibleFilterError("Unsupported hashlib constructor: {0}".format(algorithm))

        raw = hmac.new(
            str(secret).encode("utf-8"),
            str(message).encode("utf-8"),
            digestmod,
        ).hexdigest()

        return raw[:salt_length]
