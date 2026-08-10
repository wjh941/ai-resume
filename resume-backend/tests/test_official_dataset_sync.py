from __future__ import annotations

import asyncio
import io
import zipfile

import httpx
import pytest

from app.db import connect, initialize_database
from app.repositories.knowledgebase import KnowledgebaseRepository
from app.services.official_dataset_sync import OfficialDatasetSyncService


@pytest.fixture
def sync_service():
    return OfficialDatasetSyncService(repository=object())


def test_static_parser_normalizes_csv_json_and_zip_payloads(sync_service):
    csv_rows = sync_service.parse_static_payload(
        "职业名称,职业大类\n数据治理工程师,信息技术\n",
        file_format="csv",
    )
    json_rows = sync_service.parse_static_payload(
        '[{"专业名称":"数据管理与应用","专业门类":"管理学"}]',
        file_format="json",
    )
    archive_buffer = io.BytesIO()
    with zipfile.ZipFile(archive_buffer, "w") as archive:
        archive.writestr("official.csv", "职业名称,职业大类\n算法评测工程师,人工智能\n")
    zip_rows = sync_service.parse_static_payload(
        archive_buffer.getvalue(),
        file_format="zip",
    )

    assert csv_rows == [{"职业名称": "数据治理工程师", "职业大类": "信息技术"}]
    assert json_rows == [{"专业名称": "数据管理与应用", "专业门类": "管理学"}]
    assert zip_rows == [{"职业名称": "算法评测工程师", "职业大类": "人工智能"}]


def test_static_parser_rejects_html_and_unsafe_zip_entries(sync_service):
    with pytest.raises(ValueError, match="HTML"):
        sync_service.parse_static_payload("<html>not a dataset</html>", file_format="csv")

    archive_buffer = io.BytesIO()
    with zipfile.ZipFile(archive_buffer, "w") as archive:
        archive.writestr("../unsafe.csv", "职业名称\n不应导入\n")

    with pytest.raises(ValueError, match="安全"):
        sync_service.parse_static_payload(archive_buffer.getvalue(), file_format="zip")


def test_sync_downloads_direct_csv_and_marks_new_role_as_official_dataset(tmp_path):
    database_path = tmp_path / "catalog.db"
    initialize_database(database_path)
    with connect(database_path) as connection:
        connection.execute(
            """
            INSERT INTO official_dataset_source (
                source_key, display_name, direct_url, allowed_hosts_json,
                file_format, parser_kind, enabled
            ) VALUES (?, ?, ?, ?, ?, ?, 1)
            """,
            (
                "official-test",
                "官方职业分类测试集",
                "https://data.example.gov.cn/occupations.csv",
                '["data.example.gov.cn"]',
                "csv",
                "occupation",
            ),
        )

    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            headers={"content-type": "text/csv", "etag": "v1"},
            content="职业名称,职业大类\n数据隐私治理工程师,数据与数据平台\n".encode("utf-8"),
            request=request,
        )
    )
    repository = KnowledgebaseRepository(database_path)
    service = OfficialDatasetSyncService(
        repository,
        cache_path=tmp_path / "dataset-cache",
        transport=transport,
    )

    summary = asyncio.run(service.sync())
    role = repository.get_role("数据隐私治理工程师")

    assert summary.added_roles == 1
    assert role.catalog_origin == "official_dataset"