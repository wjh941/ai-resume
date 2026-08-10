from __future__ import annotations

from app.services.official_text_parser import parse_official_text


def test_parse_official_text_extracts_roles_and_majors_from_local_file(tmp_path):
    source = tmp_path / "official-catalog.txt"
    source.write_text(
        "\n".join(
            [
                "# 人社与教育部门公开静态文本整理",
                "职业：数据隐私治理工程师|数据与数据平台|数据合规工程师;隐私工程师",
                "专业：数据管理与应用|管理学|数据管理;信息管理",
                "无效行",
            ]
        ),
        encoding="utf-8",
    )

    result = parse_official_text(source)

    assert result.roles == [
        {
            "role_name": "数据隐私治理工程师",
            "family": "数据与数据平台",
            "aliases": ["数据合规工程师", "隐私工程师"],
        }
    ]
    assert result.majors == [
        {
            "major_name": "数据管理与应用",
            "category": "管理学",
            "aliases": ["数据管理", "信息管理"],
        }
    ]
