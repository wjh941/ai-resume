from __future__ import annotations

import re

from pydantic import BaseModel, Field, field_validator


_PHONE_PATTERN = re.compile(r"^1[3-9]\d{9}$")
_ACCOUNT_PATTERN = re.compile(r"^[a-z][a-z0-9_.-]{2,31}$")


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


class PasswordCredentialsRequest(BaseModel):
    account: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=10, max_length=72)

    @field_validator("account")
    @classmethod
    def validate_account(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not _ACCOUNT_PATTERN.fullmatch(normalized):
            raise ValueError("账号需为 3-32 位小写英文字母、数字或 ._-")
        return normalized

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if not 10 <= len(value.encode("utf-8")) <= 72:
            raise ValueError("密码长度需为 10-72 个字节")
        return value


class AuthUser(BaseModel):
    user_id: str
    phone: str
    role: str
    account: str | None = None


class PhoneLoginResult(BaseModel):
    token: str
    user: AuthUser
