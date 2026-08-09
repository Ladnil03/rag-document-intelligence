"""Password hashing + JWT encode/decode.

The FastAPI dependency that turns a Bearer token into a ``User`` row
lives in ``app.api.deps`` because it is HTTP-layer concern; this
module owns only the cryptographic primitives.
"""

import logging
from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

from app.core import config

logger = logging.getLogger(__name__)
password_hasher = PasswordHash.recommended()


class AuthenticationConfigurationError(RuntimeError):
    """Raised when JWT configuration is missing or unusable."""


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return password_hasher.verify(password, password_hash)


def create_access_token(user_id: int) -> str:
    if not config.JWT_SECRET_KEY:
        raise AuthenticationConfigurationError("JWT_SECRET_KEY is not configured.")
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    return jwt.encode(
        {"sub": str(user_id), "exp": expires_at},
        config.JWT_SECRET_KEY,
        algorithm=config.JWT_ALGORITHM,
    )


def decode_access_token(token: str) -> int:
    """Return the user id encoded in a Bearer JWT, or raise on failure.

    The caller (``app.api.deps.get_current_user``) translates the
    exception into a 401 response.
    """
    from jwt.exceptions import InvalidTokenError
    payload = jwt.decode(
        token,
        config.JWT_SECRET_KEY,
        algorithms=[config.JWT_ALGORITHM],
        options={"require": ["sub", "exp"]},
    )
    return int(payload["sub"])
