from __future__ import annotations

from app.config import Settings
from app.repositories.push_logs import PushLogRepository, PushSendLog


class PushDispatcher:
    _targets = ("sms", "wechat_subscription")

    def __init__(self, settings: Settings, logs: PushLogRepository) -> None:
        self._logs = logs
        self._mode = settings.push_dispatcher_mode

    @property
    def mode(self) -> str:
        return self._mode

    def dispatch(
        self,
        event_type: str,
        user_id: str,
        source_ref: str,
        payload: dict[str, object],
    ) -> list[PushSendLog]:
        logs: list[PushSendLog] = []
        for target_type in self._targets:
            if self._logs.exists_for_source(event_type, target_type, source_ref):
                continue
            # TODO: Provider invocation is deferred until production integration is approved.
            log = self._logs.create(
                event_type,
                user_id,
                source_ref,
                target_type,
                self._mode,
                "sent" if self._mode == "mock" else "skipped",
                payload,
            )
            if log is not None:
                logs.append(log)
        return logs
