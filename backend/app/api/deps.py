"""HTTP-layer dependencies shared across routes.

Lives under ``app.api`` because it is FastAPI-specific glue. The
cryptographic primitives it composes live in ``app.core.security``.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import AuthenticationConfigurationError, decode_access_token
from app.crud.users import get_user_by_id
from app.db.base import get_db
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)


def _credentials_exception() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Validate a Bearer JWT and return the corresponding active user row."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _credentials_exception()

    from app.core import config

    if not config.JWT_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication is not configured.",
        )

    try:
        user_id = decode_access_token(credentials.credentials)
    except Exception:
        # InvalidTokenError + KeyError + ValueError + TypeError all map to
        # "could not validate credentials" — never leak the underlying cause.
        raise _credentials_exception() from None

    user = get_user_by_id(db, user_id)
    if not user:
        raise _credentials_exception()
    return user
