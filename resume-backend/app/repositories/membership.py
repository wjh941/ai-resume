from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

from app.db import connect


class OrderNotFoundError(Exception):
    pass


class OrderExpiredError(Exception):
    pass


class PaymentCallbackConflictError(Exception):
    pass


@dataclass(frozen=True)
class VipRecord:
    vip_level: str
    expire_time: str | None
    auto_renew: bool


@dataclass(frozen=True)
class OrderRecord:
    order_id: str
    package_type: str
    total_amount: int
    payment_status: str
    payment_channel: str | None
    provider_transaction_id: str | None
    create_time: str
    entitlement_expire_time: str | None

    def as_dict(self) -> dict[str, object]:
        return {
            "order_id": self.order_id,
            "package_type": self.package_type,
            "total_amount": self.total_amount,
            "payment_status": self.payment_status,
            "payment_channel": self.payment_channel,
            "provider_transaction_id": self.provider_transaction_id,
            "create_time": self.create_time,
            "entitlement_expire_time": self.entitlement_expire_time,
        }


class MembershipRepository:
    """一期 SQLite 会员仓储；所有入口均显式接收 JWT 派生的 user_id。"""

    def __init__(self, database_path: Path) -> None:
        self._database_path = database_path

    def current_vip(self, user_id: str) -> VipRecord:
        now = datetime.now(timezone.utc)
        with connect(self._database_path) as connection:
            row = connection.execute(
                "SELECT vip_level, expire_time, auto_renew FROM user_vip WHERE user_id = ?",
                (user_id,),
            ).fetchone()
            if row is None:
                connection.execute(
                    """
                    INSERT INTO user_vip (user_id, vip_level, expire_time, auto_renew, create_time)
                    VALUES (?, 'free', NULL, 0, ?)
                    """,
                    (user_id, now.isoformat()),
                )
                return VipRecord("free", None, False)

            expire_time = str(row["expire_time"]) if row["expire_time"] else None
            if row["vip_level"] != "free" and _is_expired(expire_time, now):
                # 自动续费仅是未来扩展点，本期绝不自动扣款或续期。
                connection.execute(
                    """
                    UPDATE user_vip
                    SET vip_level = 'free', expire_time = NULL, auto_renew = 0
                    WHERE user_id = ?
                    """,
                    (user_id,),
                )
                return VipRecord("free", None, False)
            return VipRecord(str(row["vip_level"]), expire_time, bool(row["auto_renew"]))

    def create_order(
        self,
        user_id: str,
        package_type: str,
        total_amount: int,
        auto_renew: bool,
    ) -> OrderRecord:
        now = datetime.now(timezone.utc).isoformat()
        order_id = f"ORD{datetime.now(timezone.utc):%Y%m%d%H%M%S}{uuid4().hex[:10].upper()}"
        with connect(self._database_path) as connection:
            connection.execute(
                """
                INSERT INTO order_record
                (order_id, user_id, package_type, total_amount, payment_status, create_time, payment_channel, entitlement_expire_time, auto_renew)
                VALUES (?, ?, ?, ?, 'pending', ?, NULL, NULL, ?)
                """,
                (order_id, user_id, package_type, total_amount, now, int(auto_renew)),
            )
        return self.get_order(user_id, order_id)

    def get_order(self, user_id: str, order_id: str) -> OrderRecord:
        with connect(self._database_path) as connection:
            row = connection.execute(
                "SELECT * FROM order_record WHERE order_id = ? AND user_id = ?",
                (order_id, user_id),
            ).fetchone()
        if row is None:
            raise OrderNotFoundError(order_id)
        return self._order_from_row(row)

    def expire_pending_orders(self, user_id: str, expire_minutes: int) -> None:
        cutoff = (datetime.now(timezone.utc) - timedelta(minutes=expire_minutes)).isoformat()
        with connect(self._database_path) as connection:
            connection.execute(
                """
                UPDATE order_record
                SET payment_status = 'expired'
                WHERE user_id = ? AND payment_status = 'pending' AND create_time <= ?
                """,
                (user_id, cutoff),
            )

    def expire_all_pending_orders(self, expire_minutes: int) -> int:
        cutoff = (datetime.now(timezone.utc) - timedelta(minutes=expire_minutes)).isoformat()
        with connect(self._database_path) as connection:
            cursor = connection.execute(
                """
                UPDATE order_record
                SET payment_status = 'expired'
                WHERE payment_status = 'pending' AND create_time <= ?
                """,
                (cutoff,),
            )
        return int(cursor.rowcount)

    def list_expired_orders(self) -> list[dict[str, str]]:
        with connect(self._database_path) as connection:
            rows = connection.execute(
                """
                SELECT order_id, user_id, package_type
                FROM order_record
                WHERE payment_status = 'expired'
                ORDER BY create_time ASC, order_id ASC
                """
            ).fetchall()
        return [
            {
                "order_id": str(row["order_id"]),
                "user_id": str(row["user_id"]),
                "package_type": str(row["package_type"]),
            }
            for row in rows
        ]

    def expire_all_pending_orders(self, expire_minutes: int) -> int:
        cutoff = (datetime.now(timezone.utc) - timedelta(minutes=expire_minutes)).isoformat()
        with connect(self._database_path) as connection:
            cursor = connection.execute(
                """
                UPDATE order_record
                SET payment_status = 'expired'
                WHERE payment_status = 'pending' AND create_time <= ?
                """,
                (cutoff,),
            )
        return int(cursor.rowcount)

    def list_orders(self, user_id: str) -> list[OrderRecord]:
        with connect(self._database_path) as connection:
            rows = connection.execute(
                "SELECT * FROM order_record WHERE user_id = ? ORDER BY create_time DESC, order_id DESC",
                (user_id,),
            ).fetchall()
        return [self._order_from_row(row) for row in rows]

    def fulfill_order(
        self,
        user_id: str,
        order_id: str,
        payment_channel: str,
        target_level: str,
        duration_days: int,
        expire_minutes: int,
        provider_transaction_id: str | None = None,
    ) -> tuple[OrderRecord, VipRecord]:
        now = datetime.now(timezone.utc)
        with connect(self._database_path) as connection:
            connection.execute(
                """
                UPDATE order_record
                SET payment_status = 'expired'
                WHERE user_id = ? AND payment_status = 'pending' AND create_time <= ?
                """,
                (user_id, (now - timedelta(minutes=expire_minutes)).isoformat()),
            )
            row = connection.execute(
                "SELECT * FROM order_record WHERE order_id = ? AND user_id = ?",
                (order_id, user_id),
            ).fetchone()
            if row is None:
                raise OrderNotFoundError(order_id)

            if str(row["payment_status"]) == "expired":
                raise OrderExpiredError(order_id)

            current = self._current_vip_in_connection(connection, user_id, now)
            if str(row["payment_status"]) == "paid":
                existing_transaction = row["provider_transaction_id"]
                if existing_transaction and provider_transaction_id and existing_transaction != provider_transaction_id:
                    raise PaymentCallbackConflictError(order_id)
                return self._order_from_row(row), current

            base_time = _future_or_now(current.expire_time, now)
            expire_time = (base_time + timedelta(days=duration_days)).isoformat()
            vip_level = "premium" if current.vip_level == "premium" else target_level
            connection.execute(
                """
                UPDATE user_vip
                SET vip_level = ?, expire_time = ?, auto_renew = ?, create_time = ?
                WHERE user_id = ?
                """,
                (vip_level, expire_time, int(bool(row["auto_renew"])), now.isoformat(), user_id),
            )
            connection.execute(
                """
                UPDATE order_record
                SET payment_status = 'paid', payment_channel = ?, provider_transaction_id = ?, entitlement_expire_time = ?
                WHERE order_id = ? AND user_id = ?
                """,
                (payment_channel, provider_transaction_id, expire_time, order_id, user_id),
            )
            completed = connection.execute(
                "SELECT * FROM order_record WHERE order_id = ? AND user_id = ?",
                (order_id, user_id),
            ).fetchone()
        if completed is None:
            raise OrderNotFoundError(order_id)
        return self._order_from_row(completed), VipRecord(vip_level, expire_time, bool(row["auto_renew"]))

    def _current_vip_in_connection(self, connection, user_id: str, now: datetime) -> VipRecord:
        row = connection.execute(
            "SELECT vip_level, expire_time, auto_renew FROM user_vip WHERE user_id = ?", (user_id,)
        ).fetchone()
        if row is None:
            connection.execute(
                """
                INSERT INTO user_vip (user_id, vip_level, expire_time, auto_renew, create_time)
                VALUES (?, 'free', NULL, 0, ?)
                """,
                (user_id, now.isoformat()),
            )
            return VipRecord("free", None, False)
        expire_time = str(row["expire_time"]) if row["expire_time"] else None
        if row["vip_level"] != "free" and _is_expired(expire_time, now):
            connection.execute(
                "UPDATE user_vip SET vip_level = 'free', expire_time = NULL, auto_renew = 0 WHERE user_id = ?",
                (user_id,),
            )
            return VipRecord("free", None, False)
        return VipRecord(str(row["vip_level"]), expire_time, bool(row["auto_renew"]))

    @staticmethod
    def _order_from_row(row) -> OrderRecord:
        return OrderRecord(
            order_id=str(row["order_id"]),
            package_type=str(row["package_type"]),
            total_amount=int(row["total_amount"]),
            payment_status=str(row["payment_status"]),
            payment_channel=str(row["payment_channel"]) if row["payment_channel"] else None,
            provider_transaction_id=(
                str(row["provider_transaction_id"])
                if row["provider_transaction_id"]
                else None
            ),
            create_time=str(row["create_time"]),
            entitlement_expire_time=(
                str(row["entitlement_expire_time"])
                if row["entitlement_expire_time"]
                else None
            ),
        )


def _is_expired(expire_time: str | None, now: datetime) -> bool:
    if not expire_time:
        return True
    return datetime.fromisoformat(expire_time).astimezone(timezone.utc) <= now


def _future_or_now(expire_time: str | None, now: datetime) -> datetime:
    if expire_time and not _is_expired(expire_time, now):
        return datetime.fromisoformat(expire_time).astimezone(timezone.utc)
    return now
