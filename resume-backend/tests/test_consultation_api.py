from __future__ import annotations


def assert_success(response):
    assert response.status_code == 200
    assert response.json()["code"] == "ok"
    return response.json()["data"]


def make_text_pdf(text: str) -> bytes:
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>"
        ),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        f"<< /Length {len(f'BT /F1 18 Tf 72 720 Td ({text}) Tj ET'.encode())} >>\n"
        f"stream\nBT /F1 18 Tf 72 720 Td ({text}) Tj ET\nendstream".encode(),
    ]
    document = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for number, content in enumerate(objects, start=1):
        offsets.append(len(document))
        document.extend(f"{number} 0 obj\n".encode())
        document.extend(content)
        document.extend(b"\nendobj\n")
    xref_offset = len(document)
    document.extend(f"xref\n0 {len(objects) + 1}\n".encode())
    document.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        document.extend(f"{offset:010d} 00000 n \n".encode())
    document.extend(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF\n"
        ).encode()
    )
    return bytes(document)


def test_job_analysis_returns_nine_sections_and_detailed_identity_plan(api_client):
    data = assert_success(
        api_client.post(
            "/api/consultation/job-analysis",
            json={"role_name": "Data Engineer", "identity_code": "2"},
        )
    )

    assert data["identity_code"] == "2"
    assert data["identity_label"] == "应届毕业生（秋招/春招）"
    assert len(data["job_analysis_sections"]) == 9
    assert [section["order"] for section in data["job_analysis_sections"]] == list(range(1, 10))
    assert data["job_analysis_sections"][0]["title"] == "基础工作"
    assert data["job_analysis_sections"][8]["title"] == "岗位避雷点"
    assert data["identity_plan"]["title"] == "应届毕业生全套求职解决方案"
    assert len(data["identity_plan"]["sections"]) >= 7
    assert data["market_notice"] == "本地演示模式：薪资与市场信息为参考估算，请结合目标城市和企业招聘信息核验。"
    assert data["job_intelligence"]["role_name"] == "Data Engineer"


def test_job_analysis_returns_growth_route_risk_markers_and_custom_requirement_notes(api_client):
    data = assert_success(
        api_client.post(
            "/api/consultation/job-analysis",
            json={
                "role_name": "Data Engineer",
                "identity_code": "2",
                "custom_requirement": "Prioritize Hangzhou roles with weekends off",
            },
        )
    )

    route = data["career_growth_route"]
    assert route["title"] == "职业晋升路线"
    assert [stage["stage"] for stage in route["stages"]] == ["初级", "中级", "高级"]
    assert all(stage["role_name"] for stage in route["stages"])
    assert all(stage["years_reference"] for stage in route["stages"])
    assert all(stage["core_skills"] for stage in route["stages"])
    assert all(stage["responsibilities"] for stage in route["stages"])
    assert all(stage["assessment_criteria"] for stage in route["stages"])
    assert any(
        item.startswith("【避雷】") or item.startswith("【高频坑】")
        for item in data["job_analysis_sections"][8]["items"]
    )
    assert "Prioritize Hangzhou roles with weekends off" in " ".join(data["custom_requirement_notes"])


def test_all_identities_receive_distinct_detailed_plans(api_client):
    expected_titles = {
        "1": "在校学生全套求职解决方案",
        "2": "应届毕业生全套求职解决方案",
        "3": "在职跳槽全套求职解决方案",
        "4": "待业求职全套求职解决方案",
        "5": "零基础转行全套求职解决方案",
    }

    for identity_code, expected_title in expected_titles.items():
        data = assert_success(
            api_client.post(
                "/api/consultation/job-analysis",
                json={"role_name": "Data Engineer", "identity_code": identity_code},
            )
        )
        assert data["identity_plan"]["title"] == expected_title
        assert len(data["identity_plan"]["sections"]) >= 6


def test_job_analysis_rejects_unknown_identity_code(api_client):
    response = api_client.post(
        "/api/consultation/job-analysis",
        json={"role_name": "Data Engineer", "identity_code": "6"},
    )

    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"


def test_resume_review_returns_safe_full_resume_and_interview_intro(api_client):
    data = assert_success(
        api_client.post(
            "/api/consultation/resume-review",
            json={
                "identity_code": "5",
                "role_name": "Data Engineer",
                "resume_text": "曾负责团队日常数据整理和报表制作。",
            },
        )
    )

    assert data["identity_code"] == "5"
    assert data["identity_label"] == "零基础跨行业转行"
    assert data["issues"]
    assert data["rewrite_examples"]
    assert data["keywords"]
    assert "[待确认]" in data["optimized_resume_text"]
    assert "Data Engineer" in data["interview_intro"]
    assert "job_analysis_sections" not in data
    assert "identity_plan" not in data


def test_resume_review_returns_transparent_match_report_and_custom_requirement_notes(api_client):
    data = assert_success(
        api_client.post(
            "/api/consultation/resume-review",
            json={
                "identity_code": "2",
                "role_name": "Data Engineer",
                "resume_text": "Built SQL reports for the operations team.",
                "custom_requirement": "Focus on entry-level data platform roles.",
            },
        )
    )

    report = data["job_match_report"]
    assert 0 <= report["score"] <= 100
    assert report["score_basis"]
    assert report["matching_advantages"]
    assert report["missing_skills"]
    assert report["priority_gaps"]
    assert all(gap["skill_name"] for gap in report["priority_gaps"])
    assert all(gap["learning_direction"] for gap in report["priority_gaps"])
    assert all(gap["project_practice"] for gap in report["priority_gaps"])
    assert all(gap["practice_task"] for gap in report["priority_gaps"])
    assert "Focus on entry-level data platform roles." in " ".join(data["custom_requirement_notes"])


def test_resume_review_rejects_blank_text(api_client):
    response = api_client.post(
        "/api/consultation/resume-review",
        json={"identity_code": "1", "resume_text": "   "},
    )

    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"


def test_advice_returns_structured_salary_negotiation_guidance(api_client):
    data = assert_success(
        api_client.post(
            "/api/consultation/advice",
            json={
                "identity_code": "3",
                "role_name": "Data Engineer",
                "topic": "salary_negotiation",
                "question": "我应该如何确认年终奖和公积金？",
            },
        )
    )

    assert data["topic"] == "salary_negotiation"
    assert data["title"] == "薪资谈判话术"
    assert len(data["sections"]) >= 2
    assert "公积金" in " ".join(item for section in data["sections"] for item in section["items"])


def test_all_toolkit_topics_include_actions_templates_and_risk_checks(api_client):
    topics = [
        "simulation_interview",
        "salary_negotiation",
        "contract_pitfalls",
        "career_planning",
        "certificate_recommendation",
        "role_comparison",
        "written_test",
        "job_channels",
        "scam_screening",
    ]

    for topic in topics:
        data = assert_success(
            api_client.post(
                "/api/consultation/advice",
                json={
                    "identity_code": "2",
                    "role_name": "数据工程师",
                    "topic": topic,
                    "question": "请给我可以立刻执行的具体步骤。",
                },
            )
        )

        titles = [section["title"] for section in data["sections"]]
        assert len(data["sections"]) >= 5
        assert "落地行动清单" in titles
        assert "可复制表达" in titles
        assert "验证与避坑" in titles
        assert all(section["items"] for section in data["sections"])


def test_advice_rejects_unsupported_topic(api_client):
    response = api_client.post(
        "/api/consultation/advice",
        json={"identity_code": "3", "topic": "unknown"},
    )

    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"


def test_pdf_extract_returns_uploaded_resume_text(api_client):
    response = api_client.post(
        "/api/consultation/resume-pdf-extract",
        files={"file": ("resume.pdf", make_text_pdf("Resume Summary"), "application/pdf")},
    )

    data = assert_success(response)
    assert data["text"] == "Resume Summary"


def test_pdf_extract_accepts_pdf_filename_when_mobile_mime_is_generic(api_client):
    response = api_client.post(
        "/api/consultation/resume-pdf-extract",
        files={"file": ("resume.pdf", make_text_pdf("Mobile Resume"), "application/octet-stream")},
    )

    data = assert_success(response)
    assert data["text"] == "Mobile Resume"


def test_pdf_extract_rejects_non_pdf_files(api_client):
    response = api_client.post(
        "/api/consultation/resume-pdf-extract",
        files={"file": ("resume.txt", b"not a pdf", "text/plain")},
    )

    assert response.status_code == 422
