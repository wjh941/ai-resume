from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from app.schemas.auth import AuthUser, PhoneCodeRequest, PhoneLoginRequest
from app.schemas.common import success
from app.services.auth import (
    AuthenticationError,
    DemoAuthenticationDisabledError,
    current_user_id,
    optional_bearer_token,
)


router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/send-code")
def send_code(payload: PhoneCodeRequest, request: Request):
    settings = request.app.state.settings
    if settings.auth_demo_mode:
        # 本期过渡代码：仅开发演示返回固定验证码，严禁在线上生产环境开启。
        return success({"phone": payload.phone, "demo_code": "123456", "message": "演示验证码已生成"})
    # 待完善点位：根据 SMS_PROVIDER 分支接入阿里云、腾讯云或自定义 HTTP 短信网关。
    raise HTTPException(status_code=503, detail="短信服务未配置，当前禁止模拟验证码登录")


@router.post("/login-phone")
def login_phone(payload: PhoneLoginRequest, request: Request):
    try:
        token, user = request.app.state.auth_service.issue_phone_login(payload.phone, payload.code)
    except DemoAuthenticationDisabledError as error:
        raise HTTPException(status_code=503, detail="真实短信登录尚未配置") from error
    except AuthenticationError as error:
        raise HTTPException(status_code=401, detail="手机号或验证码错误") from error
    return success({"token": token, "user": AuthUser(user_id=user.user_id, phone=user.phone).model_dump()})


@router.post("/wx-login")
def wechat_login(request: Request):
    settings = request.app.state.settings
    # 待完善点位：需配置微信开放平台 AppID、AppSecret、HTTPS 回调域名后实现 OAuth 回调。
    if not (settings.wechat_open_app_id and settings.wechat_open_app_secret and settings.wechat_open_redirect_uri):
        raise HTTPException(status_code=503, detail="微信开放平台参数未配置，扫码登录暂不可用")
    raise HTTPException(status_code=501, detail="微信扫码授权回调尚未启用")


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
    return success(AuthUser(user_id=user.user_id, phone=user.phone).model_dump())
