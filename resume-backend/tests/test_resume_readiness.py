from app.schemas.resume import ResumePayload
from app.services.resume_readiness import inspect_resume_readiness
from conftest import make_resume_payload


def test_readiness_blocks_missing_contact_and_warns_pending_text():
    payload = make_resume_payload()
    payload["basic"]["name"] = ""
    payload["basic"]["phone"] = ""
    payload["projects"][0]["description"] = "[待确认] 需要补充真实结果"
    resume = ResumePayload.model_validate(payload)

    report = inspect_resume_readiness(resume)

    assert "姓名" in report.blocking_items
    assert "手机号" in report.blocking_items
    assert any("[待确认]" in item for item in report.warning_items)
    assert report.ready is False


def test_readiness_does_not_mutate_the_resume_payload():
    resume = ResumePayload.model_validate(make_resume_payload())
    original = resume.model_dump(mode="json")

    report = inspect_resume_readiness(resume)

    assert report.ready is True
    assert resume.model_dump(mode="json") == original
