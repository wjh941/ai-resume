from __future__ import annotations

import asyncio
import json

from app.config import Settings
from app.schemas.job import JobIntelligence
from app.services.ai_client import OpenAICompatibleClient


class CapturingClient(OpenAICompatibleClient):
    def __init__(self) -> None:
        super().__init__(
            Settings(
                app_env="test",
                app_host="127.0.0.1",
                app_port=8000,
                database_path=None,  # type: ignore[arg-type]
                ai_provider="openai_compatible",
                ai_api_key="test",
                ai_base_url="https://example.invalid/v1",
                ai_model="test",
                cache_expire_day=7,
                temp_file_path=None,  # type: ignore[arg-type]
                export_file_expire_minutes=60,
                pdf_renderer="playwright",
                playwright_browsers_path="",
            )
        )
        self.calls: list[tuple[str, str]] = []

    async def _chat_completion(self, system_prompt: str, user_prompt: str) -> str:
        self.calls.append((system_prompt, user_prompt))
        if "job_intelligence" in user_prompt:
            request = json.loads(user_prompt)
            assert "market_notice" in request["required_json_keys"]
            return json.dumps(
                {
                    "identity_code": "2",
                    "identity_label": "应届毕业生（秋招/春招）",
                    "job_intelligence": request["job_intelligence"],
                    "job_analysis_sections": [
                        {"order": index, "title": f"板块{index}", "items": ["内容"]}
                        for index in range(1, 10)
                    ],
                    "identity_plan": {
                        "title": "应届毕业生全套求职解决方案",
                        "sections": [
                            {"order": index, "title": f"方案{index}", "items": ["内容"]}
                            for index in range(1, 5)
                        ],
                    },
                    "follow_up_question": "需要继续细化吗？",
                    "market_notice": "实时市场信息需核验。",
                    "career_growth_route": {
                        "title": "职业晋升路线",
                        "stages": [
                            {
                                "stage": stage,
                                "role_name": f"{stage} Data Engineer",
                                "years_reference": "参考年限",
                                "core_skills": ["Python"],
                                "responsibilities": ["负责交付"],
                                "assessment_criteria": ["完成验收"],
                            }
                            for stage in ["初级", "中级", "高级"]
                        ],
                    },
                    "custom_requirement_notes": ["已纳入补充需求"],
                },
                ensure_ascii=False,
            )
        assert "optimized_resume_text" in system_prompt
        assert "interview_intro" in system_prompt
        return json.dumps(
            {
                "identity_code": "2",
                "identity_label": "应届毕业生（秋招/春招）",
                "issues": ["问题"],
                "rewrite_examples": ["范文"],
                "keywords": ["Python"],
                "optimized_resume_text": "草稿[待确认]",
                "interview_intro": "自我介绍",
                "job_match_report": {
                    "score": 60,
                    "score_basis": ["透明评分口径"],
                    "matching_advantages": ["已有真实素材"],
                    "missing_skills": ["SQL"],
                    "priority_gaps": [
                        {
                            "skill_name": "SQL",
                            "learning_direction": "学习方向",
                            "project_practice": "项目练习",
                            "practice_task": "练习任务",
                        }
                    ],
                },
                "custom_requirement_notes": ["已纳入补充需求"],
            },
            ensure_ascii=False,
        )


def test_openai_compatible_client_requests_all_extended_consultation_fields():
    async def run() -> None:
        client = CapturingClient()
        job = JobIntelligence(role_name="Data Engineer")

        analysis = await client.build_job_consultation(job, "2", "Prioritize Hangzhou")
        review = await client.review_resume_text(
            "resume text",
            "2",
            "Data Engineer",
            "Focus on data platform roles",
        )

        assert analysis.market_notice == "实时市场信息需核验。"
        assert review.optimized_resume_text == "草稿[待确认]"
        job_system_prompt, job_user_prompt = client.calls[0]
        review_system_prompt, review_user_prompt = client.calls[1]
        assert "career_growth_route" in job_system_prompt
        assert "custom_requirement_notes" in job_system_prompt
        assert json.loads(job_user_prompt)["custom_requirement"] == "Prioritize Hangzhou"
        assert "job_match_report" in review_system_prompt
        assert "custom_requirement_notes" in review_system_prompt
        assert json.loads(review_user_prompt)["custom_requirement"] == "Focus on data platform roles"

    asyncio.run(run())
