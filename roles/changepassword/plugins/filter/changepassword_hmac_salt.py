# -*- coding: utf-8 -*-
"""Ansible filter plugin for changepassword audit HMAC salt handling."""

from __future__ import annotations

import hashlib
import hmac


def changepassword_hmac_salt(value: object, secret: object) -> str:
    """Return a deterministic HMAC-SHA256 hex digest without exposing secrets."""
    value_bytes = str(value).encode("utf-8")
    secret_bytes = str(secret).encode("utf-8")
    return hmac.new(secret_bytes, value_bytes, hashlib.sha256).hexdigest()


class FilterModule:
    """Expose changepassword filters to Ansible."""

    def filters(self):
        return {
            "changepassword_hmac_salt": changepassword_hmac_salt,
        }
