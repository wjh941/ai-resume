from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import secrets
from typing import Callable

import httpx

from app.config import Settings


class SmsConfigurationError(Exception):
    pass


class SmsDeliveryError(Exception):
    pass


class SmsRateLimitError(Exception):
    pass


class VerificationCodeError(Exception):
    pass


@dataclass(frozen=True)
class SmsSendResult:
    demo_code: str | None
    message: str


@dataclass(frozen=True)
class _VerificationCode:
    digest: str
    expires_at: datetime


Transport = Callable[[str, dict[str, str], dict[str, str]], None]


class SmsService:
    """Development mock SMS plus a provider-neutral production HTTPS gateway."""

    def __init__(
        self,
        settings: Settings,
        *,
        code_factory: Callable[[], str] | None = None,
        transport: Transport | None = None,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self._settings = settings
        self._code_factory = code_factory or (lambda: f"{secrets.randbelow(1_000_000):06d}")
        self._transport = transport or self._send_http
        self._now = now or (lambda: datetime.now(timezone.utc))
        self._codes: dict[str, _VerificationCode] = {}
        self._last_sent_at: dict[str, datetime] = {}

    def send_code(self, phone: str) -> SmsSendResult:
        if self._settings.auth_demo_mode:
            return SmsSendResult("123456", "Development verification code generated.")

        self._validate_gateway()
        now = self._now()
        last_sent_at = self._last_sent_at.get(phone)
        if last_sent_at and now - last_sent_at < timedelta(seconds=self._settings.sms_code_cooldown_seconds):
            raise SmsRateLimitError

        code = self._code_factory()
        self._transport(
            self._settings.sms_http_endpoint,
            {
                "Authorization": f"Bearer {self._settings.sms_access_secret}",
                "X-SMS-Access-Key": self._settings.sms_access_key,
            },
            {
                "phone": phone,
                "code": code,
                "sign_name": self._settings.sms_sign_name,
                "template_id": self._settings.sms_template_id,
            },
        )
        self._codes[phone] = _VerificationCode(
            self._digest(phone, code),
            now + timedelta(seconds=self._settings.sms_code_ttl_seconds),
        )
        self._last_sent_at[phone] = now
        return SmsSendResult(None, "Verification code sent.")

    def verify_code(self, phone: str, code: str) -> None:
        if self._settings.auth_demo_mode:
            if code != "123456":
                raise VerificationCodeError
            return

        entry = self._codes.get(phone)
        if entry is None or entry.expires_at <= self._now():
            self._codes.pop(phone, None)
            raise VerificationCodeError
        if not hmac.compare_digest(entry.digest, self._digest(phone, code)):
            raise VerificationCodeError
        self._codes.pop(phone, None)

    def _validate_gateway(self) -> None:
        if self._settings.sms_provider != "http":
            raise SmsConfigurationError
        if not all((
            self._settings.sms_http_endpoint,
            self._settings.sms_access_key,
            self._settings.sms_access_secret,
            self._settings.sms_sign_name,
            self._settings.sms_template_id,
        )):
            raise SmsConfigurationError

    def _digest(self, phone: str, code: str) -> str:
        return hmac.new(
            self._settings.jwt_secret.encode("utf-8"),
            f"{phone}:{code}".encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    @staticmethod
    def _send_http(url: str, headers: dict[str, str], payload: dict[str, str]) -> None:
        try:
            response = httpx.post(url, headers=headers, json=payload, timeout=10.0)
            response.raise_for_status()
        except httpx.HTTPError as error:
            raise SmsDeliveryError from error
