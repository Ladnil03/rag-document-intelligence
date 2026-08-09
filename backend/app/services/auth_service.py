"""Auth-related business logic.

Routes call into this service so they stay thin. The actual JWT/password
primitives still live in ``app.core.security``.
"""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import (
    AuthenticationConfigurationError,
    create_access_token,
    hash_password,
    verify_password,
)
from app.crud.users import create_user, get_user_by_email, get_user_by_id
from app.models.user import User
from app.schemas.auth import TokenResponse, UserRegistration


class EmailAlreadyExistsError(Exception):
    """Raised when registration collides with an existing user."""


class InvalidCredentialsError(Exception):
    """Raised when login email/password do not match."""


class AuthenticationUnavailableError(Exception):
    """Raised when JWT signing is not configured."""


def register_user(db: Session, registration: UserRegistration) -> User:
    if get_user_by_email(db, registration.email):
        raise EmailAlreadyExistsError(registration.email)
    try:
        return create_user(
            db,
            email=registration.email,
            password_hash=hash_password(registration.password.get_secret_value()),
        )
    except IntegrityError:
        # The database unique constraint handles a concurrent registration.
        raise EmailAlreadyExistsError(registration.email) from None


def authenticate(db: Session, email: str, password: str) -> TokenResponse:
    user = get_user_by_email(db, email)
    if not user or not verify_password(password, user.password_hash):
        raise InvalidCredentialsError()
    try:
        token = create_access_token(user.id)
    except AuthenticationConfigurationError as exc:
        raise AuthenticationUnavailableError() from exc
    return TokenResponse(access_token=token)


def load_user(db: Session, user_id: int) -> User | None:
    return get_user_by_id(db, user_id)
