from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from app.repositories.membership import OrderNotFoundError
from app.schemas.common import success
from app.schemas.membership import CreateOrderPayload, PaymentCallbackPayload
from app.services.auth import current_user_id
from app.services.membership import VipStatus, get_current_vip


router = APIRouter(tags=["membership"])


@router.get("/api/user/vip-info")
def vip_info(vip: VipStatus = Depends(get_current_vip)):
    return success(vip.as_dict())


@router.get("/api/pay/package-list")
def package_list(request: Request, _: str = Depends(current_user_id)):
    return success({"items": request.app.state.membership_service.list_packages()})


@router.post("/api/pay/create-order")
def create_order(
    payload: CreateOrderPayload,
    request: Request,
    user_id: str = Depends(current_user_id),
):
    return success(
        request.app.state.membership_service.create_order(
            user_id, payload.package_type, payload.auto_renew
        ).as_dict()
    )


@router.post("/api/pay/callback")
def payment_callback(
    payload: PaymentCallbackPayload,
    request: Request,
    user_id: str = Depends(current_user_id),
):
    order, vip = request.app.state.membership_service.fulfill_payment(
        user_id,
        payload.order_id,
        payload.payment_channel,
        payload.provider_transaction_id,
        payload.signature,
    )
    return success({"order": order.as_dict(), "vip": vip.as_dict()})


@router.get("/api/user/order-list")
def order_list(request: Request, user_id: str = Depends(current_user_id)):
    return success({"items": request.app.state.membership_service.list_orders(user_id)})
