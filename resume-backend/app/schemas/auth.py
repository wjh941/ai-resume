from __future__ import annotations

import re

from pydantic import BaseModel, Field, field_validator


_PHONE_PATTERN = re.compile(r"^1[3-9]\d{9}$")


class PhoneCodeRequest(BaseModel):
    phone: str = Field(min_length=11, max_length=20)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        normalized = "".join(value.split())
        if not _PHONE_PATTERN.fullmatch(normalized):
            raise ValueError("phone must be a mainland China mobile number")
        return normalized


class PhoneLoginRequest(PhoneCodeRequest):
    code: str = Field(min_length=4, max_length=12)

    @field_validator("code")
    @classmethod
    def validate_code(cls, value: str) -> str:
        normalized = "".join(value.split())
        if not normalized.isdigit():
            raise ValueError("verification code must contain only digits")
        return normalized


class AuthUser(BaseModel):
    user_id: str
    phone: str
    role: str


class PhoneLoginResult(BaseModel):
    token: str
    user: AuthUser
