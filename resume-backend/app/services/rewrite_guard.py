from __future__ import annotations

import re

from app.schemas.resume import ResumePayload


_METRIC_PATTERN = re.compile(r"\d+(?:[.,]\d+)?")


class RewriteFactViolation(ValueError):
    pass


def _metrics(resume: ResumePayload) -> list[str]:
    text_parts = [resume.self_evaluation]
    text_parts.extend(item.description for item in resume.employment)
    text_parts.extend(item.description for item in resume.projects)
    return _METRIC_PATTERN.findall("\n".join(text_parts))


def _assert_equal(actual: object, expected: object, field_name: str) -> None:
    if actual != expected:
        raise RewriteFactViolation(f"AI rewrite changed immutable field: {field_name}")


def validate_rewrite_facts(original: ResumePayload, rewritten: ResumePayload) -> None:
    _assert_equal(rewritten.basic, original.basic, "basic")
    _assert_equal(rewritten.job, original.job, "job")
    _assert_equal(rewritten.skills, original.skills, "skills")
    _assert_equal(rewritten.section_visibility, original.section_visibility, "section_visibility")

    _assert_equal(len(rewritten.education), len(original.education), "education length")
    for index, (before, after) in enumerate(zip(original.education, rewritten.education)):
        _assert_equal(after, before, f"education[{index}]")

    _assert_equal(len(rewritten.employment), len(original.employment), "employment length")
    for index, (before, after) in enumerate(zip(original.employment, rewritten.employment)):
        _assert_equal(after.company, before.company, f"employment[{index}].company")
        _assert_equal(after.position, before.position, f"employment[{index}].position")
        _assert_equal(after.start_date, before.start_date, f"employment[{index}].start_date")
        _assert_equal(after.end_date, before.end_date, f"employment[{index}].end_date")

    _assert_equal(len(rewritten.projects), len(original.projects), "projects length")
    for index, (before, after) in enumerate(zip(original.projects, rewritten.projects)):
        _assert_equal(after.name, before.name, f"projects[{index}].name")
        _assert_equal(after.role, before.role, f"projects[{index}].role")
        _assert_equal(after.start_date, before.start_date, f"projects[{index}].start_date")
        _assert_equal(after.end_date, before.end_date, f"projects[{index}].end_date")

    _assert_equal(_metrics(rewritten), _metrics(original), "stated metrics")
