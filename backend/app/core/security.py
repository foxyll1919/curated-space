"""Password hashing and session tokens.

Passwords use PBKDF2-HMAC-SHA256 from the standard library rather than a new
dependency: it is memory-hard enough for a single-user library, needs no native
build on Windows, and keeps `build.md`'s "no new heavy dependencies" rule. The
encoded form carries its own parameters, so the iteration count can be raised
later without invalidating existing hashes.

Session tokens are random 32-byte values handed to the browser in an httpOnly
cookie. Only their SHA-256 digest is stored, so a database copy does not hand
over live sessions.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets


ALGORITHM = "pbkdf2_sha256"
SALT_BYTES = 16
TOKEN_BYTES = 32
# OWASP's 2023 floor for PBKDF2-HMAC-SHA256. Tests lower this; production does not.
DEFAULT_ITERATIONS = 600_000


def _b64(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _unb64(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def hash_password(password: str, *, iterations: int = DEFAULT_ITERATIONS) -> str:
    """Return `algorithm$iterations$salt$hash`, all components base64url."""
    salt = secrets.token_bytes(SALT_BYTES)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"{ALGORITHM}${iterations}${_b64(salt)}${_b64(digest)}"


def verify_password(password: str, encoded: str) -> bool:
    """Constant-time verification that never raises on a malformed hash.

    A row whose hash cannot be parsed verifies as False rather than crashing a
    login request, which also keeps a corrupted row indistinguishable from a
    wrong password to the caller.
    """
    try:
        algorithm, iterations_raw, salt_raw, digest_raw = encoded.split("$")
        if algorithm != ALGORITHM:
            return False
        salt = _unb64(salt_raw)
        expected = _unb64(digest_raw)
        iterations = int(iterations_raw)
    except (ValueError, TypeError):
        return False
    candidate = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return hmac.compare_digest(candidate, expected)


def new_session_token() -> str:
    return secrets.token_urlsafe(TOKEN_BYTES)


def hash_session_token(token: str) -> str:
    """Digest stored in place of the token; the cookie keeps the raw value."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
