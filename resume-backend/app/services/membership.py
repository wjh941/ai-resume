from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, Request

from app.config import Settings
from app.repositories.membership import MembershipRepository, OrderRecord, VipRecord
from app.services.auth import current_user_id


class VipPermissionError(Exception):
    def __init__(self, message: str = "当前会员等级暂不支持该功能") -> None:
        super().__init__(message)
        self.message = message


class PaymentDemoDisabledError(Exception):
    pass


class MembershipPackageConflictError(Exception):
    pass


class PaymentChannelUnavailableError(Exception):
    """真实支付验签尚未接入时的明确服务端提示，不能伪装成会员权限不足。"""

    pass


@dataclass(frozen=True)
class PackageDefinition:
    package_type: str
    name: str
    vip_level: str
    duration_days: int
    total_amount: int
    benefits: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "package_type": self.package_type,
            "name": self.name,
            "vip_level": self.vip_level,
            "duration_days": self.duration_days,
            "total_amount": self.total_amount,
            "benefits": list(self.benefits),
        }


PACKAGES: dict[str, PackageDefinition] = {
    "monthly": PackageDefinition(
        "monthly", "月度基础会员", "basic", 30, 2900,
        ("不限简历草稿", "最多对比 4 个岗位", "完整匹配报告与测评"),
    ),
    "quarterly": PackageDefinition(
        "quarterly", "季度基础会员", "basic", 90, 7900,
        ("不限简历草稿", "最多对比 4 个岗位", "一次经历批量导出"),
    ),
    "annual": PackageDefinition(
        "annual", "年度高级会员", "premium", 365, 19900,
        ("全部功能解锁", "无水印导出", "完整题库与长期文件存储"),
    ),
}


@dataclass(frozen=True)
class VipStatus:
    vip_level: str
    expire_time: str | None
    auto_renew: bool

    @property
    def max_drafts(self) -> int | None:
        return 3 if self.vip_level == "free" else None

    @property
    def max_compare_jobs(self) -> int:
        return 2 if self.vip_level == "free" else 4

    @property
    def watermark_text(self) -> str | None:
        return {"free": "Resume Dashboard Free", "basic": "Resume Dashboard Basic"}.get(self.vip_level)

    def allows(self, feature: str) -> bool:
        if feature in {"full_job_report", "full_assessment", "bulk_evidence_export"}:
            return self.vip_level in {"basic", "premium"}
        if feature in {"watermark_free_export", "industry_insight", "interview_bank", "multi_draft_compare", "bulk_all_data"}:
            return self.vip_level == "premium"
        return True

    def as_dict(self) -> dict[str, object]:
        return {
            "vip_level": self.vip_level,
            "expire_time": self.expire_time,
            "auto_renew": self.auto_renew,
            "max_drafts": self.max_drafts,
            "max_compare_jobs": self.max_compare_jobs,
        }


class MembershipService:
    """一期会员权限服务；二期迁移数据库时仅替换仓储，不改变路由依赖契约。"""

    def __init__(self, repository: MembershipRepository, settings: Settings) -> None:
        self._repository = repository
        self._settings = settings

    def current_vip(self, user_id: str) -> VipStatus:
        if not self._settings.membership_enabled:
            return VipStatus("premium", None, False)
        return self._status_from_record(self._repository.current_vip(user_id))

    def list_packages(self) -> list[dict[str, object]]:
        return [package.as_dict() for package in PACKAGES.values()]

    def create_order(self, user_id: str, package_type: str, auto_renew: bool) -> OrderRecord:
        package = PACKAGES[package_type]
        current = self.current_vip(user_id)
        if current.vip_level == "premium" and package.vip_level != "premium":
            # 活跃高级会员不能以基础套餐价格延长高级权益；到期后会自动降级再按基础套餐购买。
            raise MembershipPackageConflictError
        return self._repository.create_order(user_id, package_type, package.total_amount, auto_renew)

    def fulfill_payment(self, user_id: str, order_id: str, payment_channel: str) -> tuple[OrderRecord, VipStatus]:
        # 模拟回调在生产环境绝不允许由配置反向开启，避免任何登录用户自行完成订单。
        if payment_channel == "demo" and (
            self._settings.app_env.strip().lower() == "production"
            or not self._settings.payment_demo_mode
        ):
            raise PaymentDemoDisabledError
        if payment_channel != "demo":
            # 后续在这里校验微信支付/支付宝签名；未配置商户密钥时不允许伪造成功回调。
            raise PaymentChannelUnavailableError
        order = self._repository.get_order(user_id, order_id)
        package = PACKAGES[order.package_type]
        completed, status = self._repository.fulfill_order(
            user_id, order_id, payment_channel, package.vip_level, package.duration_days
        )
        return completed, self._status_from_record(status)

    def list_orders(self, user_id: str) -> list[dict[str, object]]:
        return [order.as_dict() for order in self._repository.list_orders(user_id)]

    @staticmethod
    def _status_from_record(record: VipRecord) -> VipStatus:
        return VipStatus(record.vip_level, record.expire_time, record.auto_renew)


def get_current_vip(request: Request, user_id: str = Depends(current_user_id)) -> VipStatus:
    """全业务路由统一执行到期降级，并且只信任 JWT 的 user_id。"""
    return request.app.state.membership_service.current_vip(user_id)


def require_vip_feature(feature: str):
    def dependency(vip: VipStatus = Depends(get_current_vip)) -> VipStatus:
        if not vip.allows(feature):
            raise VipPermissionError
        return vip
    return dependency
