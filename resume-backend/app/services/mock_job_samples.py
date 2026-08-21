from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MockJobSample:
    company: str
    city: str
    salary_range: str
    responsibilities: tuple[str, ...]
    requirements: tuple[str, ...]
    match_score_reference: int


MOCK_JOB_SAMPLES: dict[str, MockJobSample] = {
    "后端开发工程师": MockJobSample(
        company="星桥云服务（模拟）",
        city="杭州",
        salary_range="14k-22k（模拟参考）",
        responsibilities=("维护核心业务接口", "参与服务稳定性优化"),
        requirements=("Python或Java", "SQL", "HTTP API", "Git"),
        match_score_reference=76,
    ),
    "数据分析师": MockJobSample(
        company="澄明数据科技（模拟）",
        city="上海",
        salary_range="12k-18k（模拟参考）",
        responsibilities=("维护业务指标体系", "完成专题数据分析"),
        requirements=("SQL", "Python", "数据可视化"),
        match_score_reference=78,
    ),
    "算法工程师": MockJobSample(
        company="智序人工智能（模拟）",
        city="北京",
        salary_range="18k-30k（模拟参考）",
        responsibilities=("训练并评估模型效果", "协同推进算法服务落地"),
        requirements=("Python", "机器学习", "概率统计", "模型评估"),
        match_score_reference=72,
    ),
    "行政专员": MockJobSample(
        company="远帆企业服务（模拟）",
        city="广州",
        salary_range="6k-9k（模拟参考）",
        responsibilities=("协调日常行政事务", "维护办公与供应商台账"),
        requirements=("Excel", "文档处理", "沟通协调", "流程执行"),
        match_score_reference=74,
    ),
    "财务专员": MockJobSample(
        company="恒准财务咨询（模拟）",
        city="深圳",
        salary_range="8k-13k（模拟参考）",
        responsibilities=("整理凭证与报表资料", "协助完成费用与账务核对"),
        requirements=("会计基础", "Excel", "财务软件", "细致核对"),
        match_score_reference=75,
    ),
}


def get_mock_job_sample(role_name: str) -> MockJobSample | None:
    return MOCK_JOB_SAMPLES.get(role_name)
