from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from app.repositories.password_accounts import PasswordAccountExistsError
from app.schemas.auth import AuthUser, PasswordCredentialsRequest, PhoneCodeRequest, PhoneLoginRequest
from app.schemas.common import success
from app.services.auth import (
    AuthenticationError,
    current_user_id,
    optional_bearer_token,
)
from app.services.sms import SmsConfigurationError, SmsDeliveryError, SmsRateLimitError, VerificationCodeError


router = APIRouter(prefix="/api/auth", tags=["auth"])


def _auth_response(token: str, user, account: str | None = None):
    return success({
        "token": token,
        "user": AuthUser(
            user_id=user.user_id,
            phone=user.phone,
            role=user.role,
            account=account,
        ).model_dump(exclude_none=True),
    })


@router.post("/send-code")
def send_code(payload: PhoneCodeRequest, request: Request):
    try:
        result = request.app.state.sms_service.send_code(payload.phone)
    except SmsRateLimitError as error:
        raise HTTPException(status_code=429, detail="Please wait before requesting another verification code.") from error
    except (SmsConfigurationError, SmsDeliveryError) as error:
        raise HTTPException(status_code=503, detail="SMS delivery is not configured or temporarily unavailable.") from error
    return success({"phone": payload.phone, "demo_code": result.demo_code, "message": result.message})


@router.post("/login-phone")
def login_phone(payload: PhoneLoginRequest, request: Request):
    try:
        request.app.state.sms_service.verify_code(payload.phone, payload.code)
        token, user = request.app.state.auth_service.issue_phone_login(payload.phone)
    except (VerificationCodeError, AuthenticationError) as error:
        raise HTTPException(status_code=401, detail="Mobile number or verification code is invalid.") from error
    return _auth_response(token, user)


@router.post("/register-password")
def register_password(payload: PasswordCredentialsRequest, request: Request):
    try:
        token, user = request.app.state.auth_service.register_password_account(
            payload.account, payload.password
        )
    except PasswordAccountExistsError as error:
        raise HTTPException(status_code=409, detail="账号已存在，请直接登录。") from error
    return _auth_response(token, user, payload.account)


@router.post("/login-password")
def login_password(payload: PasswordCredentialsRequest, request: Request):
    try:
        token, user = request.app.state.auth_service.login_password_account(
            payload.account, payload.password
        )
    except AuthenticationError as error:
        raise HTTPException(status_code=401, detail="账号或密码错误。") from error
    return _auth_response(token, user, payload.account)


@router.post("/wx-login")
def wechat_login(request: Request):
    settings = request.app.state.settings
    # 待完善点位：需配置微信开放平台 AppID、AppSecret、HTTPS 回调域名后实现 OAuth 回调。
    if not (settings.wechat_open_app_id and settings.wechat_open_app_secret and settings.wechat_open_redirect_uri):
        raise HTTPException(status_code=503, detail="微信开放平台参数未配置，扫码登录暂不可用")
    raise HTTPException(status_code=501, detail="微信扫码授权回调尚未启用")


@router.get("/wechat/callback")
def wechat_callback(request: Request, code: str | None = None, state: str | None = None):
    settings = request.app.state.settings
    if not (settings.wechat_open_app_id and settings.wechat_open_app_secret and settings.wechat_open_redirect_uri):
        raise HTTPException(status_code=503, detail="WeChat Open Platform is not configured.")
    # TODO: Exchange the callback code only after the HTTPS redirect domain is whitelisted in WeChat Open Platform.
    raise HTTPException(status_code=501, detail="WeChat OAuth callback deployment requires an HTTPS whitelisted redirect domain.")


@router.post("/logout")
def logout(request: Request, token: str | None = Depends(optional_bearer_token)):
    if token is not None:
        try:
            request.app.state.auth_service.logout(token)
        except AuthenticationError as error:
            raise HTTPException(status_code=401, detail="Authentication is invalid or expired") from error
    return success({"logged_out": True})


@router.get("/me")
def current_user(request: Request, user_id: str = Depends(current_user_id)):
    user = request.app.state.auth_service.get_user(user_id)
    return success(
        AuthUser(
            user_id=user.user_id,
            phone=user.phone,
            role=user.role,
            account=request.app.state.auth_service.get_password_account(user_id),
        ).model_dump(exclude_none=True)
    )
