from __future__ import annotations

from app.schemas.consultation import (
    AdviceTopic,
    CareerAdviceResponse,
    CareerGrowthRoute,
    CareerGrowthStage,
    IDENTITY_LABELS,
    ConsultationSection,
    IdentityCode,
    IdentityPlan,
    JobMatchReport,
    JobConsultationResponse,
    PrioritySkillGap,
    ResumeReviewResponse,
)
from app.schemas.job import JobIntelligence


def build_job_consultation(
    job: JobIntelligence,
    identity_code: IdentityCode,
    custom_requirement: str | None = None,
) -> JobConsultationResponse:
    role_name = job.role_name
    salary = job.salary_by_experience
    analysis = [
        ConsultationSection(
            order=1,
            title="基础工作",
            items=[
                f"{role_name}的日常重点是：{_join(job.responsibilities)}",
                "典型流程是接收业务目标、拆解任务、交付结果、复盘优化；上下班和办公环境以目标公司制度为准。",
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
                f"0-1年与1-3年参考：{salary.get('1-3_years', '以目标城市招聘信息为准')}；3-5年参考：{salary.get('3-5_years', '以目标城市招聘信息为准')}。",
                f"5年以上参考：{salary.get('5_plus_years', '以目标城市招聘信息为准')}。",
                "底薪、绩效、年终奖、餐补交通住房、五险一金缴纳基数与绩效扣减规则需在面试和 offer 阶段逐项确认。",
            ],
        ),
        ConsultationSection(
            order=3,
            title="硬性准入门槛",
            items=[
                f"常见学历与项目门槛：{_join(job.hard_requirements)}",
                f"必备技能：{_join(job.required_skills)}。",
                f"加分技能：{_join(job.bonus_skills)}。",
                "证书不是唯一门槛，但应把能证明技能的课程项目、作品链接或实践成果写清楚。",
            ],
        ),
        ConsultationSection(
            order=4,
            title="隐性软要求",
            items=[
                "面试通常会观察沟通是否清晰：能否用业务语言解释技术或方法选择。",
                "企业会看抗压与协作：是否能拆解任务、同步风险、按节点交付。",
                "请准备一个从问题定位、行动过程到结果复盘的 STAR 案例，避免只讲“参与过”。",
            ],
        ),
        ConsultationSection(
            order=5,
            title="双晋升通道",
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
        ConsultationSection(
            order=9,
            title="岗位避雷点",
            items=[
                "警惕以培训、贷款、押金、收费内推为前提的岗位；正规招聘不会要求先付款。",
                "面试时确认劳动合同主体、社保缴纳地、试用期、加班补偿和绩效计算方式，避免口头承诺。",
                "对“高薪但岗位职责模糊”“无固定办公地”“要求先交个人证件原件”的公司保持谨慎。",
            ],
        ),
    ]
    analysis[3] = ConsultationSection(
        order=analysis[3].order,
        title=analysis[3].title,
        items=[
            *analysis[3].items,
            "隐性筛选还包括优先级判断：面对多个需求时，能否说明取舍依据、影响范围和向谁同步决策。",
            "面对模糊任务时，面试官会追问你如何澄清目标、定义验收标准、留存过程证据并复盘改进。",
        ],
    )
    analysis[5] = ConsultationSection(
        order=analysis[5].order,
        title=analysis[5].title,
        items=[
            *analysis[5].items,
            "判断行业前景时应同时查看岗位数量、技能迭代速度和业务预算：岗位多不等于初级机会多，需区分初级执行岗与独立交付岗。",
            "建议每月保存目标城市 20 条真实 JD，统计重复出现的工具、业务场景和年限门槛，再据此调整简历关键词与学习优先级。",
        ],
    )
    risk_section = analysis[8]
    analysis[8] = ConsultationSection(
        order=risk_section.order,
        title=risk_section.title,
        items=[
            f"【避雷】{risk_section.items[0]}",
            f"【高频坑】{risk_section.items[1]}",
            f"【避雷】{risk_section.items[2]}",
            "【高频坑】不要只听“综合月薪”或“发展空间”，应要求书面确认固定薪资、绩效条件、发薪日、试用期折扣和实际汇报对象。",
        ],
    )
    career_growth_route = _build_career_growth_route(job)
    custom_requirement_notes = _custom_requirement_notes(custom_requirement)
    return JobConsultationResponse(
        identity_code=identity_code,
        career_growth_route=career_growth_route,
        custom_requirement_notes=custom_requirement_notes,
        identity_label=IDENTITY_LABELS[identity_code],
        job_intelligence=job,
        job_analysis_sections=analysis,
        identity_plan=_identity_plan(identity_code, role_name),
        follow_up_question="需要我结合你目标城市、大厂/中小企业再细化薪资与要求吗？",
        market_notice="本地演示模式：薪资与市场信息为参考估算，请结合目标城市和企业招聘信息核验。",
    )


def build_resume_review(
    resume_text: str,
    identity_code: IdentityCode,
    role_name: str | None,
    custom_requirement: str | None = None,
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
    job_match_report = _build_job_match_report(resume_text, target, keywords)
    custom_requirement_notes = _custom_requirement_notes(custom_requirement)
    return ResumeReviewResponse(
        identity_code=identity_code,
        job_match_report=job_match_report,
        custom_requirement_notes=custom_requirement_notes,
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
        optimized_resume_text=(
            f"## {target} 简历精简草稿\n"
            f"- 求职目标：{target}\n"
            f"- 核心关键词：{_join(keywords, ' / ')}\n"
            f"- 经历素材：{first_line[:120]}\n"
            f"- 优化表述：围绕[业务场景]，使用[{keywords[0]}]完成[具体动作]，"
            "沉淀[交付物]，结果为[待确认]。\n"
            "- 证明材料：补充作品链接、项目截图、复盘文档或可联系证明人[待确认]。"
        ),
        interview_intro=(
            f"面试官您好，我目前以{target}为求职方向。"
            f"我已梳理过往经历中与{_join(keywords[:2], '、')}相关的真实素材，"
            "并准备通过具体项目说明自己的行动、协作方式和可核验结果。"
            "其中尚未确认的数据会在后续补齐，不会夸大个人贡献。"
        ),
    )


def _identity_plan(identity_code: IdentityCode, role_name: str) -> IdentityPlan:
    plan_title, section_definitions = {
        "1": (
            "在校学生全套求职解决方案",
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
                ("证书取舍", [
                    "优先选择与目标岗位直接相关、招聘 JD 高频出现的证书；没有岗位关联的泛证书不应挤占项目时间。",
                ]),
                ("面试配套", [
                    "30秒自我介绍模板：我是[学校/专业]学生，围绕目标岗位完成了[真实课程项目]，希望通过实习把[技能]用于真实业务。",
                ]),
                ("3个月规划", [
                    "第1月补基础并做小作品；第2月完善项目证据与简历；第3月集中投递、模拟面试并复盘反馈。",
                ]),
                ("空白补救", [
                    "无经历时只写真实完成的课程作业、公开练习或社团任务，附上作品链接，不虚构公司实习。",
                ]),
            ],
        ),
        "2": (
            "应届毕业生全套求职解决方案",
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
                ("笔试考点", [
                    f"围绕{_join(_keywords_for_target(role_name))}梳理基础题、场景题和项目复盘题；刷题后记录错因而非只记答案。",
                ]),
                ("证书规划", [
                    "优先报名招聘描述明确要求的证书；没有真实项目时，证书不能替代作品和可追问经历。",
                ]),
                ("面试全套", [
                    "1分钟自我介绍按“专业背景-相关项目-目标岗位-可验证准备”展开；群面优先承担结构化记录和推进角色。",
                ]),
            ],
        ),
        "3": (
            "在职跳槽全套求职解决方案",
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
                ("薪资谈判", [
                    "可复制话术：我更关注职责范围、固定薪资、奖金规则、双休与公积金基数能否形成完整匹配，请明确写入 offer。",
                ]),
                ("合同避雷", [
                    "确认试用期是否符合法定期限、违约金是否有合法依据、竞业范围与补偿是否明确；不理解的条款应书面提问。",
                ]),
                ("中长期规划", [
                    "1年形成独立交付能力，3年争取负责复杂模块或项目推进；每次跳槽都要能解释能力增长逻辑。",
                ]),
            ],
        ),
        "4": (
            "待业求职全套求职解决方案",
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
                ("投递节奏", [
                    "每周固定两次集中投递、两次复盘；避免一天海投后长时间不跟进，优先提高匹配度。",
                ]),
                ("过渡思路", [
                    "可以考虑真实的中小公司、短期项目或灵活就业作为过渡，但要判断岗位是否能积累目标能力。",
                ]),
            ],
        ),
        "5": (
            "零基础转行全套求职解决方案",
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
                ("替代岗位", [
                    "同步关注同赛道的助理、运营支持、实施、测试或数据助理等入口岗位，前提是职责能积累目标能力。",
                ]),
                ("证书取舍", [
                    "只投入招聘 JD 明确要求或行业强制准入的证书；其余时间优先做能被面试追问的真实作品。",
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


def build_career_advice(
    identity_code: IdentityCode,
    topic: AdviceTopic,
    role_name: str | None,
    question: str | None,
) -> CareerAdviceResponse:
    role = role_name or "目标岗位"
    question_hint = f"你当前关注的问题：{question}" if question else "未提供具体问题时，先按下面清单逐项准备。"
    title, sections = {
        "simulation_interview": (
            "模拟面试",
            [
                ("开场准备", [f"请用1分钟说明你为何匹配{role}，结构为背景、真实项目、目标和可验证证据。", question_hint]),
                ("高频追问", ["准备一个真实 STAR 案例：问题、行动、协作、结果；未知数据写[待确认]，不要补造。", "回答后复盘是否说清职责边界和个人贡献。"]),
            ],
        ),
        "salary_negotiation": (
            "薪资谈判话术",
            [
                ("确认清单", ["请明确固定月薪、绩效占比、年终奖规则、加班补偿、双休、年假和公积金缴纳基数。", question_hint]),
                ("可复制话术", ["我希望综合职责范围、固定薪资、奖金规则和公积金基数评估 offer，方便请您说明每一项的书面口径吗？", "在信息完整前不要只用一个总包数字做决定。"]),
            ],
        ),
        "contract_pitfalls": (
            "劳动合同避坑",
            [
                ("重点条款", ["核对合同主体、工作地点、岗位、试用期、薪资构成、社保缴纳与加班安排。", "竞业协议应明确范围、期限与补偿；不理解的条款先要求书面解释。"]),
                ("风险信号", ["要求先交押金、培训费、证件原件或签署空白文件，应立即停止流程并保留沟通记录。", question_hint]),
            ],
        ),
        "career_planning": (
            "职业规划",
            [
                ("3个月", [f"围绕{role}补齐一个可展示作品、一次简历迭代和至少两轮模拟面试。", "每周记录投递反馈，按拒绝原因调整关键词与项目表达。"]),
                ("1-3年", ["第1年建立稳定交付；第2年独立负责模块；第3年承担复杂协作或领域深度。", question_hint]),
            ],
        ),
        "certificate_recommendation": (
            "证书推荐与取舍",
            [
                ("筛选原则", ["只优先考虑招聘 JD 高频要求、行业准入或目标企业明确认可的证书。", "证书不能替代真实作品、项目复盘和可追问技能。"]),
                ("行动建议", [f"先收集{role}的10条真实 JD，再决定是否投入考试成本。", question_hint]),
            ],
        ),
        "role_comparison": (
            "岗位横向对比",
            [
                ("对比维度", ["按核心产出、技能门槛、工作节奏、薪资结构、晋升路线和风险逐项对比。", "不要只看标题，应对比实际 JD 与合同主体。"]),
                ("提问模板", [f"请补充要比较的两个岗位名称，我会按{role}相关性给出差异清单。", question_hint]),
            ],
        ),
        "written_test": (
            "笔试高频题与刷题渠道",
            [
                ("准备方向", [f"围绕{_join(_keywords_for_target(role))}准备基础概念、场景题、逻辑题和项目复盘题。", "每道错题记录错因、适用场景和复盘日期。"]),
                ("投递配套", ["企业官网、校招平台、就业中心和正规内推渠道优先；不购买来源不明题库。", question_hint]),
            ],
        ),
        "job_channels": (
            "招聘渠道与内推",
            [
                ("渠道优先级", ["企业官网、国央企官方招聘平台、学校就业中心、正规招聘平台和可信内推。", "投递后记录岗位链接、版本、联系人和反馈日期。"]),
                ("避坑", ["任何收费内推、保证 offer、培训贷或要求私下转账的信息都不应继续。", question_hint]),
            ],
        ),
        "scam_screening": (
            "识别外包与求职陷阱",
            [
                ("核验动作", ["核对公司统一社会信用代码、合同主体、社保主体、办公地址和岗位职责是否一致。", "面试中直接确认是否外包、项目驻场、加班制度和绩效扣减规则。"]),
                ("高风险信号", ["无偿试岗、收费培训、押证件、高薪画饼、职责极度模糊或拒绝提供书面 offer。", question_hint]),
            ],
        ),
    }[topic]
    return CareerAdviceResponse(
        identity_code=identity_code,
        identity_label=IDENTITY_LABELS[identity_code],
        topic=topic,
        title=title,
        sections=[
            ConsultationSection(order=index, title=section_title, items=items)
            for index, (section_title, items) in enumerate(sections, start=1)
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


def _build_career_growth_route(job: JobIntelligence) -> CareerGrowthRoute:
    core_skills = job.required_skills or _keywords_for_target(job.role_name)
    advanced_skills = job.bonus_skills or core_skills
    return CareerGrowthRoute(
        title="职业晋升路线",
        stages=[
            CareerGrowthStage(
                stage="初级",
                role_name=f"初级{job.role_name}",
                years_reference="0-2年：完成基础训练并能在指导下稳定交付",
                core_skills=core_skills[:3] or core_skills,
                responsibilities=[
                    "在明确需求和业务规范下完成负责模块，及时暴露风险并提交可复核产物。",
                    "整理需求、过程记录和复盘材料，形成可写入简历的真实项目证据。",
                ],
                assessment_criteria=[
                    "交付物能按验收标准通过检查，返工原因可说明并能在复盘后减少重复问题。",
                    "能清楚说明个人负责边界、使用工具和真实结果，未知数据明确标记[待确认]。",
                ],
            ),
            CareerGrowthStage(
                stage="中级",
                role_name=f"{job.role_name}（独立负责模块）",
                years_reference="2-5年：可独立拆解复杂模块并推动跨角色协作",
                core_skills=list(dict.fromkeys([*core_skills, *advanced_skills]))[:5],
                responsibilities=[
                    "独立拆解目标、制定方案、管理关键风险，并负责从执行到复盘的完整闭环。",
                    "与产品、运营、研发或业务团队协调优先级，推动可验证的效率或质量改善。",
                ],
                assessment_criteria=[
                    "能解释方案取舍、资源约束和风险预案，并用过程数据或交付证据证明结果。",
                    "遇到模糊需求时可主动澄清验收标准，减少依赖他人反复推动。",
                ],
            ),
            CareerGrowthStage(
                stage="高级",
                role_name=f"高级{job.role_name} / 专家",
                years_reference="5年以上：承担复杂问题、方法沉淀与团队影响力",
                core_skills=list(dict.fromkeys([*advanced_skills, *core_skills]))[:6],
                responsibilities=[
                    "主导跨团队复杂项目或关键能力建设，将个人方法沉淀为可复用流程、标准或平台能力。",
                    "培养成员并参与关键决策，平衡业务目标、质量、成本、合规与长期专业债务。",
                ],
                assessment_criteria=[
                    "能持续解决高不确定性问题，并将成果转化为可复用的组织能力而非单次救火。",
                    "能带动协作方形成一致目标，清晰呈现投入、风险、收益和后续演进计划。",
                ],
            ),
        ],
    )


def _build_job_match_report(
    resume_text: str,
    target: str,
    keywords: list[str],
) -> JobMatchReport:
    normalized_text = resume_text.casefold()
    matched = [skill for skill in keywords if skill.casefold() in normalized_text]
    missing = [skill for skill in keywords if skill not in matched]
    core_skills = keywords[:3]
    supporting_skills = keywords[3:]
    core_score = round(60 * sum(skill in matched for skill in core_skills) / max(len(core_skills), 1))
    support_score = round(
        20 * sum(skill in matched for skill in supporting_skills) / max(len(supporting_skills), 1)
    )
    material_score = 20 if len(resume_text.strip()) >= 40 else 10
    score = min(100, material_score + core_score + support_score)
    visible_missing = missing or ["可核验成果材料"]
    matching_advantages = (
        [f"已在简历中识别到与{target}相关的技能证据：{_join(matched, '、')}。"]
        if matched
        else ["已提供可用于提炼的真实经历素材；下一步应补齐目标岗位所需的技能证据和项目细节。"]
    )
    priority_gaps = [
        PrioritySkillGap(
            skill_name=skill,
            learning_direction=f"围绕{skill}完成从基础概念、常用工具到业务场景的连续练习。",
            project_practice=f"完成一个贴近{target}的小型项目，保留需求、过程、产物和复盘，不虚构公司经历。",
            practice_task=f"为{skill}整理3个可追问的真实案例：做了什么、为什么这样做、证据或数据[待确认]。",
        )
        for skill in visible_missing[:3]
    ]
    return JobMatchReport(
        score=score,
        score_basis=[
            f"简历素材完整度：{material_score}/20（根据已提供文本长度与可提炼经历判断）。",
            f"核心技能覆盖：{core_score}/60（目标关键词：{_join(core_skills, '、')}）。",
            f"加分技能覆盖：{support_score}/20（目标关键词：{_join(supporting_skills, '、')}）。",
            "总分是关键词与可用经历素材覆盖度，不代表录用概率；真实项目证据和面试表现需另行核验。",
        ],
        matching_advantages=matching_advantages,
        missing_skills=visible_missing,
        priority_gaps=priority_gaps,
    )


def _custom_requirement_notes(custom_requirement: str | None) -> list[str]:
    if not custom_requirement:
        return []
    return [
        f"已纳入你的补充需求：{custom_requirement}",
        "补充需求会影响建议优先级；涉及薪资、城市、工时或企业制度的信息仍需以真实 JD、面试和书面 offer 为准。",
    ]


def _join(values: list[str], separator: str = "；") -> str:
    return separator.join(value for value in values if value) or "以目标公司招聘要求为准"
