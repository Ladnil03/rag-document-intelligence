"""Public registration and login endpoints."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.schemas.auth import TokenResponse, UserLogin, UserRegistration, UserResponse
from app.services.auth_service import (
    AuthenticationUnavailableError,
    EmailAlreadyExistsError,
    InvalidCredentialsError,
    authenticate,
    register_user,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    registration: UserRegistration,
    db: Session = Depends(get_db),
) -> UserResponse:
    """Register a user and persist only a recommended password hash."""
    try:
        user = register_user(db, registration)
    except EmailAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with that email already exists.",
        )
    return UserResponse.model_validate(user)


@router.post("/login", response_model=TokenResponse)
def login(
    credentials_payload: UserLogin,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Validate credentials and issue a short-lived Bearer access token."""
    try:
        return authenticate(
            db,
            credentials_payload.email,
            credentials_payload.password.get_secret_value(),
        )
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except AuthenticationUnavailableError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication is not configured.",
        )
