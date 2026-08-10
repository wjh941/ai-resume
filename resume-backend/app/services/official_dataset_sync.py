from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import urlparse
import zipfile

import httpx

from app.repositories.knowledgebase import KnowledgebaseRepository
from app.schemas.knowledgebase import KnowledgeSyncSummary, OfficialDatasetSource


class OfficialDatasetSyncService:
    """Downloads and parses only pre-approved static data files, never web pages."""

    max_dataset_bytes = 50 * 1024 * 1024

    def __init__(
        self,
        repository: KnowledgebaseRepository,
        *,
        cache_path: Path | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._repository = repository
        self._cache_path = cache_path or Path("./data/dataset-cache").resolve()
        self._transport = transport

    async def sync(self) -> KnowledgeSyncSummary:
        run_id = self._repository.create_sync_run("official")
        added_roles = 0
        added_majors = 0
        skipped_rows = 0
        errors: list[str] = []
        for source in self._repository.list_enabled_sources():
            try:
                payload, version = await self._download_source(source)
                rows = self.parse_static_payload(payload, file_format=source.file_format)
                source_roles, source_majors, source_skipped = self._import_rows(source, rows, version)
                added_roles += source_roles
                added_majors += source_majors
                skipped_rows += source_skipped
            except ValueError as exc:
                errors.append(f"{source.source_key}: {exc}")
            except httpx.HTTPError:
                errors.append(f"{source.source_key}: 官方静态数据集下载失败")
        status = "partial" if errors else "completed"
        return self._repository.complete_sync_run(
            run_id,
            status=status,
            added_roles=added_roles,
            added_majors=added_majors,
            skipped_rows=skipped_rows,
            errors=errors,
        )

    async def _download_source(self, source: OfficialDatasetSource) -> tuple[bytes, str]:
        if not source.direct_url:
            raise ValueError("未配置官方静态文件直链")
        parsed = urlparse(source.direct_url)
        if parsed.scheme != "https" or not parsed.hostname:
            raise ValueError("数据源必须使用 HTTPS 直链")
        allowed_hosts = {host.lower() for host in source.allowed_hosts}
        if parsed.hostname.lower() not in allowed_hosts:
            raise ValueError("数据源主机不在允许列表")
        async with httpx.AsyncClient(
            timeout=20.0,
            follow_redirects=False,
            transport=self._transport,
        ) as client:
            response = await client.get(source.direct_url)
        if 300 <= response.status_code < 400:
            raise ValueError("数据源不允许重定向")
        response.raise_for_status()
        payload = response.content
        if not payload or len(payload) > self.max_dataset_bytes:
            raise ValueError("数据集为空或超过大小限制")
        self._cache_path.mkdir(parents=True, exist_ok=True)
        digest = hashlib.sha256(payload).hexdigest()
        (self._cache_path / f"{source.source_key}-{digest[:12]}.{source.file_format}").write_bytes(payload)
        return payload, response.headers.get("etag") or digest

    def _import_rows(
        self,
        source: OfficialDatasetSource,
        rows: list[dict[str, str]],
        version: str,
    ) -> tuple[int, int, int]:
        added_roles = 0
        added_majors = 0
        skipped_rows = 0
        for row in rows:
            if source.parser_kind not in {"occupation", "employment"}:
                skipped_rows += 1
                continue
            role_name = self._first_value(row, "职业名称", "职业", "岗位名称", "名称", "role_name", "name")
            family = self._first_value(row, "职业大类", "职业类别", "岗位大类", "category", "family") or "其他"
            if not role_name:
                skipped_rows += 1
                continue
            if self._repository.upsert_system_role(
                role_name=role_name,
                family=family,
                source_key=source.source_key,
                source_version=version,
                source_url=source.direct_url or "",
            ):
                added_roles += 1
        return added_roles, added_majors, skipped_rows

    @staticmethod
    def _first_value(row: dict[str, str], *keys: str) -> str:
        for key in keys:
            value = str(row.get(key, "")).strip()
            if value:
                return value
        return ""

    def parse_static_payload(
        self,
        payload: str | bytes,
        *,
        file_format: str,
    ) -> list[dict[str, str]]:
        raw_bytes = payload.encode("utf-8") if isinstance(payload, str) else payload
        text = raw_bytes.decode("utf-8-sig", errors="replace")
        if "<html" in text.lower() or "<!doctype html" in text.lower():
            raise ValueError("HTML 页面不是可导入的官方静态数据集")
        if file_format == "csv":
            return self._parse_csv(text)
        if file_format == "json":
            return self._parse_json(text)
        if file_format == "zip":
            return self._parse_zip(raw_bytes)
        raise ValueError("仅支持 CSV、JSON 或包含 CSV/JSON 的 ZIP 数据集")

    @staticmethod
    def _parse_csv(text: str) -> list[dict[str, str]]:
        reader = csv.DictReader(io.StringIO(text))
        if not reader.fieldnames:
            raise ValueError("CSV 数据集缺少表头")
        return [
            {str(key).strip(): str(value or "").strip() for key, value in row.items() if key}
            for row in reader
        ]

    @staticmethod
    def _parse_json(text: str) -> list[dict[str, str]]:
        try:
            payload: Any = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError("JSON 数据集格式无效") from exc
        if isinstance(payload, dict):
            payload = payload.get("data", payload.get("rows", []))
        if not isinstance(payload, list) or not all(isinstance(row, dict) for row in payload):
            raise ValueError("JSON 数据集必须是对象数组或包含 data/rows 数组")
        return [
            {str(key).strip(): str(value or "").strip() for key, value in row.items()}
            for row in payload
        ]

    def _parse_zip(self, raw_bytes: bytes) -> list[dict[str, str]]:
        try:
            with zipfile.ZipFile(io.BytesIO(raw_bytes)) as archive:
                names = [name for name in archive.namelist() if not name.endswith("/")]
                if len(names) != 1:
                    raise ValueError("ZIP 数据集必须只包含一个 CSV 或 JSON 文件")
                name = names[0]
                path = PurePosixPath(name)
                if path.is_absolute() or ".." in path.parts or "\\" in name:
                    raise ValueError("ZIP 数据集包含不安全的文件路径")
                suffix = path.suffix.lower()
                if suffix not in {".csv", ".json"}:
                    raise ValueError("ZIP 数据集只允许包含 CSV 或 JSON 文件")
                with archive.open(name) as member:
                    member_bytes = member.read()
        except zipfile.BadZipFile as exc:
            raise ValueError("ZIP 数据集格式无效") from exc
        return self.parse_static_payload(member_bytes, file_format=suffix.removeprefix("."))