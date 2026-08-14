from __future__ import annotations

from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import Settings
from app.repositories.users import UserNotFoundError, UserRecord, UserRepository


class AuthenticationError(Exception):
    pass


class DemoAuthenticationDisabledError(Exception):
    pass


_bearer = HTTPBearer(auto_error=False)


class AuthService:
    """本期 JWT 服务；Token 只承载用户主键、版本号和过期时间。"""

    def __init__(self, settings: Settings, users: UserRepository) -> None:
        self._settings = settings
        self._users = users

    def issue_phone_login(self, phone: str, code: str) -> tuple[str, UserRecord]:
        if not self._settings.auth_demo_mode:
            # 真实短信接入点：阿里云、腾讯云或自定义 HTTP 网关校验回执后再放行登录。
            raise DemoAuthenticationDisabledError
        if code != "123456":
            raise AuthenticationError
        user = self._users.find_or_create_by_phone(phone)
        return self.issue_token(user), user

    def issue_token(self, user: UserRecord) -> str:
        expires_at = datetime.now(timezone.utc) + timedelta(hours=self._settings.jwt_expire_hours)
        return jwt.encode(
            {
                "sub": user.user_id,
                "token_version": user.token_version,
                "exp": expires_at,
            },
            self._settings.jwt_secret,
            algorithm="HS256",
        )

    def verify(self, token: str) -> str:
        try:
            payload = jwt.decode(
                token,
                self._settings.jwt_secret,
                algorithms=["HS256"],
                options={"require": ["sub", "token_version", "exp"]},
            )
            user_id = str(payload["sub"])
            token_version = int(payload["token_version"])
            user = self._users.get(user_id)
        except (jwt.PyJWTError, KeyError, TypeError, ValueError, UserNotFoundError) as error:
            raise AuthenticationError from error
        if user.token_version != token_version:
            raise AuthenticationError
        return user_id

    def logout(self, token: str) -> None:
        self._users.invalidate_tokens(self.verify(token))

    def get_user(self, user_id: str) -> UserRecord:
        try:
            return self._users.get(user_id)
        except UserNotFoundError as error:
            raise AuthenticationError from error


def current_user_id(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Security(_bearer),
) -> str:
    """统一依赖注入点：业务路由不可从请求参数读取用户身份。"""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Authentication is required")
    try:
        return request.app.state.auth_service.verify(credentials.credentials)
    except AuthenticationError as error:
        raise HTTPException(status_code=401, detail="Authentication is invalid or expired") from error


def optional_bearer_token(
    credentials: HTTPAuthorizationCredentials | None = Security(_bearer),
) -> str | None:
    """登出接口保持幂等公开；有 Token 时由路由完成服务端即时失效。"""
    if credentials is None or credentials.scheme.lower() != "bearer":
        return None
    return credentials.credentials
