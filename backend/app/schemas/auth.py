"""Authentication request / response schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator


class CredentialsBase(BaseModel):
    """Shared validation for registration and JSON login requests."""

    email: str = Field(..., min_length=3, max_length=320)
    password: SecretStr = Field(..., min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        local, separator, domain = normalized.partition("@")
        if not separator or not local or not domain or "." not in domain:
            raise ValueError("A valid email address is required.")
        return normalized


class UserRegistration(CredentialsBase):
    pass


class UserLogin(CredentialsBase):
    pass


class UserResponse(BaseModel):
    id: int
    email: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
