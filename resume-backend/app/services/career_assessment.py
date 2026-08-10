from __future__ import annotations

from collections import defaultdict
from copy import deepcopy


INTEREST_LABELS = {
    "realistic": "实践执行",
    "investigative": "分析研究",
    "artistic": "创意表达",
    "social": "沟通支持",
    "enterprising": "推动影响",
    "conventional": "组织规范",
}


_QUESTIONS = (
    {
        "key": "interest_realistic_1",
        "group": "interest",
        "dimension": "realistic",
        "title": "我愿意通过动手实践解决具体问题。",
    },
    {
        "key": "interest_investigative_1",
        "group": "interest",
        "dimension": "investigative",
        "title": "我愿意分析数据、规律或复杂问题。",
    },
    {
        "key": "interest_artistic_1",
        "group": "interest",
        "dimension": "artistic",
        "title": "我愿意用内容、设计或表达创造新方案。",
    },
    {
        "key": "interest_social_1",
        "group": "interest",
        "dimension": "social",
        "title": "我愿意理解他人需求并提供支持。",
    },
    {
        "key": "interest_enterprising_1",
        "group": "interest",
        "dimension": "enterprising",
        "title": "我愿意推动协作、说服他人并承担结果。",
    },
    {
        "key": "interest_conventional_1",
        "group": "interest",
        "dimension": "conventional",
        "title": "我愿意整理信息、建立规范并保证准确性。",
    },
    {
        "key": "style_structure_1",
        "group": "work_style",
        "dimension": "structure",
        "title": "我更适应目标明确、可以拆解步骤的工作。",
    },
    {
        "key": "style_collaboration_1",
        "group": "work_style",
        "dimension": "collaboration",
        "title": "我愿意与不同角色沟通并共同完成任务。",
    },
    {
        "key": "style_ambiguity_1",
        "group": "work_style",
        "dimension": "ambiguity",
        "title": "面对信息不完整的问题，我愿意先尝试再迭代。",
    },
    {
        "key": "evidence_sql_1",
        "group": "strength_evidence",
        "dimension": "data",
        "title": "我能举出使用 SQL、表格或数据处理工具完成任务的真实例子。",
    },
    {
        "key": "evidence_project_1",
        "group": "strength_evidence",
        "dimension": "project",
        "title": "我能讲清一个真实项目中的任务、行动和结果。",
    },
    {
        "key": "constraints_time_1",
        "group": "constraints",
        "dimension": "time",
        "title": "未来三个月我能稳定安排每周学习和求职复盘时间。",
    },
)


def assessment_questions() -> list[dict[str, object]]:
    return deepcopy(list(_QUESTIONS))


def score_assessment(answers: dict[str, int]) -> dict[str, object]:
    interest_values: dict[str, list[int]] = defaultdict(list)
    style_values: dict[str, list[int]] = defaultdict(list)
    evidence: list[str] = []
    answered = 0

    for key, raw_value in answers.items():
        if not isinstance(raw_value, int) or isinstance(raw_value, bool) or not 1 <= raw_value <= 5:
            continue
        answered += 1
        if key.startswith("interest_"):
            interest_key = key.split("_", 2)[1]
            interest_values[interest_key].append(raw_value)
        elif key.startswith("style_"):
            style_key = key.split("_", 2)[1]
            style_values[style_key].append(raw_value)

        if key == "evidence_sql_1" and raw_value >= 4:
            evidence.append("已说明具备 SQL/数据处理的基础证据")
        elif key == "evidence_project_1" and raw_value >= 4:
            evidence.append("已说明能够用真实项目任务、行动和结果支撑经历")

    top_interests = [
        {
            "key": key,
            "label": INTEREST_LABELS.get(key, key),
            "score": round(sum(values) / len(values), 2),
            "reason": f"你在{INTEREST_LABELS.get(key, key)}相关题目中给出了较高评价。",
        }
        for key, values in sorted(
            interest_values.items(),
            key=lambda item: (-sum(item[1]) / len(item[1]), item[0]),
        )
        if sum(values) / len(values) >= 4
    ][:3]
    structure_values = style_values.get("structure", [])
    structure_average = (
        sum(structure_values) / len(structure_values) if structure_values else 0
    )
    work_style_summary = (
        "你更偏好结构化、可拆解的问题处理方式。"
        if structure_average >= 4
        else "当前工作风格证据有限，建议在后续项目复盘中补充协作与问题处理方式。"
    )
    confidence_note = (
        "当前结果来自部分作答，证据不足；建议补完测评并结合真实项目复盘。"
        if answered < 5
        else "结果反映当前偏好与已说明证据，建议每次完成项目后更新一次。"
    )
    focus = top_interests[0]["label"] if top_interests else "目标岗位"
    return {
        "top_interests": top_interests,
        "work_style_summary": work_style_summary,
        "strength_evidence": evidence,
        "confidence_note": confidence_note,
        "answered_count": answered,
        "action_plan": {
            "seven_day": [
                "整理一段真实课程、项目或实习经历，并标出你负责的任务、工具和结果。",
                f"选择一个与{focus}相关的岗位，核对简历中是否出现岗位要求的三个核心关键词。",
            ],
            "thirty_day": [
                "完成一个可交付的小项目：提交 README、过程截图和结果说明，形成可展示证据。",
                "围绕目标岗位完成两次模拟面试，并记录每次无法清楚回答的问题。",
            ],
            "ninety_day": [
                "沉淀一份作品或项目复盘，说明问题、方法、结果和下一次改进点。",
                "复盘投递反馈，保留有效方向，停止持续没有反馈且不符合约束的投递。",
            ],
        },
    }