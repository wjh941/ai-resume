from __future__ import annotations

from app.schemas.consultation import (
    IDENTITY_LABELS,
    ConsultationSection,
    IdentityCode,
    IdentityPlan,
    JobConsultationResponse,
    ResumeReviewResponse,
)
from app.schemas.job import JobIntelligence


def build_job_consultation(
    job: JobIntelligence,
    identity_code: IdentityCode,
) -> JobConsultationResponse:
    role_name = job.role_name
    salary = job.salary_by_experience
    analysis = [
        ConsultationSection(
            order=1,
            title="基础概况",
            items=[
                f"{role_name}的日常重点是：{_join(job.responsibilities)}",
                "工作节奏通常随项目节点变化；上线、交付和业务高峰期可能需要加班。",
                "出差频率取决于公司业务属性，平台型与总部岗位通常较低，交付型岗位可能更高。",
                "计算机、数据、统计、信息管理等相关背景更容易匹配；跨专业应准备可验证作品。",
            ],
        ),
        ConsultationSection(
            order=2,
            title="薪酬分层",
            items=[
                f"实习/应届参考：{salary.get('graduate', '以目标城市招聘信息为准')}。",
                f"1-3年参考：{salary.get('1-3_years', '以目标城市招聘信息为准')}；3-5年参考：{salary.get('3-5_years', '以目标城市招聘信息为准')}。",
                f"5年以上参考：{salary.get('5_plus_years', '以目标城市招聘信息为准')}。",
                "年终奖、餐补、交通补贴、五险一金缴纳基数需在面试和 offer 阶段单独确认。",
            ],
        ),
        ConsultationSection(
            order=3,
            title="硬性门槛",
            items=[
                f"常见学历与项目门槛：{_join(job.hard_requirements)}",
                f"必备技能：{_join(job.required_skills)}。",
                f"加分技能：{_join(job.bonus_skills)}。",
                "证书不是唯一门槛，但应把能证明技能的课程项目、作品链接或实践成果写清楚。",
            ],
        ),
        ConsultationSection(
            order=4,
            title="软性隐性要求",
            items=[
                "面试通常会观察沟通是否清晰：能否用业务语言解释技术或方法选择。",
                "企业会看抗压与协作：是否能拆解任务、同步风险、按节点交付。",
                "请准备一个从问题定位、行动过程到结果复盘的 STAR 案例，避免只讲“参与过”。",
            ],
        ),
        ConsultationSection(
            order=5,
            title="完整晋升路线",
            items=[
                f"专业路线：{_join(job.career_route, ' → ')}。",
                "初级阶段重执行与基础质量；中级阶段需要独立负责模块；高级阶段需解决复杂问题并带动协作。",
                "管理路线通常从项目负责人与小团队管理开始，重点增加目标拆解、人才培养和跨团队推进能力。",
            ],
        ),
        ConsultationSection(
            order=6,
            title="行业前景",
            items=[
                "未来三年机会会集中在能直接支撑业务效率、自动化和数据决策的岗位能力上。",
                "红利来自可迁移的基础能力；内卷风险来自只会工具操作、缺少业务成果表达。",
                "一线与新一线城市的岗位密度通常较高，目标城市会显著影响薪资和技能偏好。",
            ],
        ),
        ConsultationSection(
            order=7,
            title="求职竞争",
            items=[
                "简历初筛常看岗位关键词、可验证项目和经历连续性，海投时淘汰率会较高。",
                f"高频面试方向：{_join(job.required_skills)}，以及一个真实项目的难点、取舍和复盘。",
                "致命扣分点包括：项目描述空泛、技能与经历不对应、夸大无法追问的成果、联系方式不完整。",
            ],
        ),
        ConsultationSection(
            order=8,
            title="岗位优缺点",
            items=[
                f"优点：{role_name}的能力可沉淀为可迁移的方法与作品，长期发展更依赖实际交付质量。",
                "痛点：需要持续学习工具与业务知识，项目节点可能带来较高时间压力。",
                "发展上限取决于能否把专业能力转化为业务影响力，并逐步承担复杂协作与决策责任。",
            ],
        ),
    ]
    return JobConsultationResponse(
        identity_code=identity_code,
        identity_label=IDENTITY_LABELS[identity_code],
        job_intelligence=job,
        job_analysis_sections=analysis,
        identity_plan=_identity_plan(identity_code, role_name),
        follow_up_question="需要我结合你目标城市、大厂/中小企业再细化薪资与要求吗？",
    )


def build_resume_review(
    resume_text: str,
    identity_code: IdentityCode,
    role_name: str | None,
) -> ResumeReviewResponse:
    target = role_name or "目标岗位"
    first_line = next((line.strip() for line in resume_text.splitlines() if line.strip()), resume_text[:80])
    identity_hint = {
        "1": "实习经历不足时，应优先补齐课程项目、社团职责和可展示作品。",
        "2": "校招简历应把毕业设计、竞赛和实习放在前面，避免只写课程名称。",
        "3": "跳槽简历应弱化事务性工作，突出职责范围、解决的问题和可核验结果。",
        "4": "空档期需用真实的学习、兼职或项目经历说明节奏，不要回避时间线。",
        "5": "转行简历应先写可迁移能力，再说明已完成的低成本实战项目。",
    }[identity_code]
    keywords = _keywords_for_target(target)
    return ResumeReviewResponse(
        identity_code=identity_code,
        identity_label=IDENTITY_LABELS[identity_code],
        issues=[
            f"目标岗位“{target}”的关键词覆盖不足，建议在技能、项目标题和成果描述中自然补充：{_join(keywords)}。",
            "经历描述目前更像职责罗列；每段至少补齐“场景、行动、工具、可核验结果”四个信息。",
            "没有已确认的数据时不要补造百分比、人数或金额；用“待确认”占位，后续替换为真实证据。",
            identity_hint,
        ],
        rewrite_examples=[
            f"原始内容概括：{first_line[:80]}",
            (
                f"可替换范文：围绕{target}的[业务场景]，使用[{keywords[0]}]完成[具体动作]，"
                "沉淀[交付物/方法]，推动[可核验结果，待确认]。"
            ),
            (
                "量化补充模板：将处理周期从[原始时长，待确认]优化至[优化后时长，待确认]，"
                "并通过[数据来源/复盘记录]核验结果。"
            ),
        ],
        keywords=keywords,
    )


def _identity_plan(identity_code: IdentityCode, role_name: str) -> IdentityPlan:
    plan_title, section_definitions = {
        "1": (
            "在校学生专属简历&求职实操方案",
            [
                ("简历优化", [
                    f"可复制模板：课程项目｜围绕{role_name}完成[项目名称]，负责[具体模块]，使用[工具]产出[可验证交付物]。",
                    "把社团、志愿或校园实践按“目标-行动-结果”改写，不要只列职务名称。",
                ]),
                ("7天技能提升", [
                    "第1-2天学习岗位核心工具；第3-4天完成一个小型作品；第5天整理项目说明；第6-7天模拟面试并迭代简历。",
                    "优先选择官方文档、公开课程和可在 GitHub/作品集展示的练习。",
                ]),
                ("求职渠道", [
                    "关注企业官网、校招平台、实习僧、BOSS直聘和校内就业中心；远程实习需核验公司主体。",
                    "实习简历控制在一页，联系方式、可到岗时间和每周可实习天数必须清楚。",
                ]),
                ("加分项", [
                    "可复制模板：在[竞赛/校园活动]中协调[人数/资源，待确认]，完成[成果]，提升[影响指标，待确认]。",
                ]),
            ],
        ),
        "2": (
            "应届生专属简历&求职实操方案",
            [
                ("简历优化", [
                    "可复制模板：在[毕业设计/竞赛]中负责[模块]，通过[方法]解决[问题]，形成[作品/报告]，结果[待确认]。",
                    "教育、毕业设计、实习和竞赛按与目标岗位的相关性排序。",
                ]),
                ("技能补齐", [
                    f"在两周内做一个紧贴{role_name}的完整小项目，保留需求、过程、截图、代码或复盘证据。",
                    "项目不是越多越好，优先准备一个可被连续追问十分钟的作品。",
                ]),
                ("求职规划", [
                    "秋招重点准备提前批与暑期实习转正；春招补充中小企业、区域龙头和国企岗位。",
                    "大厂看基础与项目深度，中小企业更看上手速度；分别准备不同版本的自我介绍。",
                ]),
                ("兜底适配", [
                    "同步关注与核心技能相邻的岗位，保持关键词与项目经历一致，避免无关海投。",
                ]),
            ],
        ),
        "3": (
            "在职跳槽专属简历&求职实操方案",
            [
                ("简历优化", [
                    "可复制模板：负责[业务范围]，识别[问题]，采用[方法/工具]推动[行动]，结果为[真实指标，待确认]。",
                    "删除纯事务性表述，将篇幅留给可量化项目与跨团队协作。",
                ]),
                ("技能补充", [
                    "按每晚45-60分钟安排：两天补基础、一周完成一个工作场景复盘、周末更新作品与简历。",
                ]),
                ("跳槽技巧", [
                    "骑驴找马时保持在职状态；谈薪以职责范围、能力证据和市场区间为依据。",
                    "背调前先核对离职证明、任职时间和项目表述，避免前后不一致。",
                ]),
                ("瓶颈风险", [
                    "若长期只做重复交付，应主动争取复杂项目、业务理解和可复用方法沉淀。",
                ]),
            ],
        ),
        "4": (
            "待业求职专属简历&求职实操方案",
            [
                ("简历优化", [
                    "空档期真实说明模板：在[起止时间]集中完成[学习/兼职/家庭事务]，同步通过[作品/课程/项目]保持岗位能力。",
                    "时间线必须真实、连续，避免用虚构公司填补空档。",
                ]),
                ("15-30天补齐计划", [
                    f"第1周梳理{role_name}能力差距；第2周完成实战作品；第3周投递与模拟面试；第4周复盘面试反馈。",
                ]),
                ("面试应答", [
                    "标准表达：空档期间我明确了求职方向，并完成了[真实行动]。现在已准备好以[能力证据]投入新岗位。",
                ]),
                ("过渡经历", [
                    "选择真实的短期项目、兼职或志愿服务补充经历，并保留联系人或成果证据。",
                ]),
            ],
        ),
        "5": (
            "零基础转行专属简历&求职实操方案",
            [
                ("简历优化", [
                    "可复制模板：原岗位中我长期使用[可迁移能力]解决[真实问题]，已通过[项目/课程]把该能力迁移到目标方向。",
                    "简历顶部先写转行目标、相关技能和作品链接，再写原经历中的共通能力。",
                ]),
                ("最低门槛学习路线", [
                    f"先掌握{_join(_keywords_for_target(role_name))}中的基础项，再完成一个可公开演示的低成本实战项目。",
                    "每个学习阶段必须留下作品、笔记或复盘，作为面试证据。",
                ]),
                ("转行面试", [
                    "标准回答：我转行不是临时决定，已完成[真实准备]并验证兴趣与能力；原经验可在[场景]中帮助团队。",
                ]),
                ("1/2/3年规划", [
                    "第1年建立可交付能力；第2年独立负责模块并形成方法；第3年向复杂项目、领域深度或带项目推进。",
                ]),
            ],
        ),
    }[identity_code]
    return IdentityPlan(
        title=plan_title,
        sections=[
            ConsultationSection(order=index, title=title, items=items)
            for index, (title, items) in enumerate(section_definitions, start=1)
        ],
    )


def _keywords_for_target(role_name: str) -> list[str]:
    normalized = role_name.casefold()
    if any(key in normalized for key in ("data", "数据", "etl", "数仓")):
        return ["Python", "SQL", "数据建模", "数据质量"]
    if any(key in normalized for key in ("frontend", "前端", "vue", "react")):
        return ["JavaScript", "TypeScript", "组件化", "性能优化"]
    if any(key in normalized for key in ("backend", "后端", "java", "服务端")):
        return ["API设计", "数据库", "稳定性", "问题排查"]
    if any(key in normalized for key in ("product", "产品")):
        return ["需求分析", "用户研究", "数据分析", "项目推进"]
    return ["岗位核心技能", "问题解决", "沟通协作", "项目复盘"]


def _join(values: list[str], separator: str = "；") -> str:
    return separator.join(value for value in values if value) or "以目标公司招聘要求为准"
