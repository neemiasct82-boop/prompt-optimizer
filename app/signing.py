"""HMAC signatures for optimized prompt versions (spec AC4a/AC4b).

The server is stateless. Each optimized prompt it issues carries a version and
an HMAC-SHA256 signature. Revise and generate only accept prompts whose text
and version match the signature, so an answer is always generated from a
prompt the server produced and the user confirmed.
"""

from __future__ import annotations

import hashlib
import hmac


def sign_prompt(secret: str, version: int, prompt: str) -> str:
    message = f"{version}\n{prompt}".encode()
    return hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()


def verify_prompt(secret: str, version: int, prompt: str, signature: str) -> bool:
    expected = sign_prompt(secret, version, prompt)
    return hmac.compare_digest(expected, signature)
