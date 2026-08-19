from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


PackageType = Literal["monthly", "quarterly", "annual"]
PaymentChannel = Literal["demo", "wechat_pay", "alipay"]


class CreateOrderPayload(BaseModel):
    package_type: PackageType
    auto_renew: bool = False


class PaymentCallbackPayload(BaseModel):
    order_id: str = Field(min_length=1, max_length=80)
    payment_channel: PaymentChannel
    payment_status: Literal["paid"] = "paid"
    provider_transaction_id: str | None = Field(default=None, max_length=160)
    signature: str | None = Field(default=None, max_length=256)
