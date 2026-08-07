from __future__ import annotations

from dataclasses import dataclass, replace
import json
import sqlite3


@dataclass(frozen=True)
class RoleSeed:
    role_name: str
    family: str
    aliases: tuple[str, ...]
    recommended_majors: tuple[str, ...]
    adjacent_majors: tuple[str, ...]
    relevant_courses: tuple[str, ...]
    required_skills: tuple[str, ...]
    entry_skills: tuple[str, ...]
    alternative_roles: tuple[str, ...]
    internship_roles: tuple[str, ...]
    entry_difficulty: int
    industry_tags: tuple[str, ...]
    description: str


@dataclass(frozen=True)
class MajorSeed:
    major_name: str
    category: str
    aliases: tuple[str, ...]
    related_families: tuple[str, ...]
    transferable_skills: tuple[str, ...]


@dataclass(frozen=True)
class FamilyDefaults:
    aliases: tuple[str, ...]
    recommended_majors: tuple[str, ...]
    adjacent_majors: tuple[str, ...]
    relevant_courses: tuple[str, ...]
    required_skills: tuple[str, ...]
    entry_skills: tuple[str, ...]
    alternative_roles: tuple[str, ...]
    internship_roles: tuple[str, ...]
    entry_difficulty: int
    industry_tags: tuple[str, ...]


ROLE_FAMILIES = (
    {"name": "软件研发", "description": "面向应用、平台与客户端的软件工程岗位。"},
    {"name": "人工智能与算法", "description": "面向模型、算法、智能应用与数据标注岗位。"},
    {"name": "数据与数据平台", "description": "面向数据开发、分析、治理和数据基础设施岗位。"},
    {"name": "测试与质量工程", "description": "面向软件、硬件与质量保障岗位。"},
    {"name": "云计算、运维与安全", "description": "面向基础设施、云平台、运维和安全岗位。"},
    {"name": "产品、项目与解决方案", "description": "面向产品规划、项目交付与企业解决方案岗位。"},
    {"name": "设计与内容创意", "description": "面向视觉、交互、内容与创意表达岗位。"},
    {"name": "市场、品牌与增长", "description": "面向营销、品牌、投放与增长岗位。"},
    {"name": "运营、电商与客户成功", "description": "面向用户、商品、平台与客户运营岗位。"},
    {"name": "销售、商务与供应链", "description": "面向销售、商务拓展、采购与供应链岗位。"},
    {"name": "财务、法务、人力与行政", "description": "面向企业职能支持与专业服务岗位。"},
    {
        "name": "机械、电子、制造、能源与生物医药",
        "description": "面向制造业、硬件、能源与医药健康岗位。",
    },
)


FAMILY_ROLE_NAMES: dict[str, tuple[str, ...]] = {
    "软件研发": (
        "后端开发工程师",
        "前端开发工程师",
        "全栈开发工程师",
        "移动端开发工程师",
        "iOS开发工程师",
        "Android开发工程师",
        "客户端开发工程师",
        "Java开发工程师",
        "Python开发工程师",
        "Go开发工程师",
        "C++开发工程师",
        ".NET开发工程师",
        "嵌入式软件工程师",
        "游戏开发工程师",
        "区块链开发工程师",
        "音视频开发工程师",
        "低代码开发工程师",
    ),
    "人工智能与算法": (
        "算法工程师",
        "机器学习工程师",
        "深度学习工程师",
        "计算机视觉工程师",
        "自然语言处理工程师",
        "推荐算法工程师",
        "搜索算法工程师",
        "大模型工程师",
        "AI Agent工程师",
        "MLOps工程师",
        "AI平台工程师",
        "数据挖掘工程师",
        "语音算法工程师",
        "AIGC工程师",
        "机器人算法工程师",
        "AI应用工程师",
        "数据标注专员",
    ),
    "数据与数据平台": (
        "数据工程师",
        "大数据开发工程师",
        "数据仓库工程师",
        "ETL工程师",
        "数据分析师",
        "BI分析师",
        "数据科学家",
        "数据库运维工程师",
        "数据治理工程师",
        "数据质量工程师",
        "数据清洗专员",
        "数据架构师",
        "数据库开发工程师",
        "实时计算工程师",
        "数据采集工程师",
        "主数据工程师",
        "数据仓库架构师",
    ),
    "测试与质量工程": (
        "测试开发工程师",
        "自动化测试工程师",
        "软件测试工程师",
        "性能测试工程师",
        "安全测试工程师",
        "测试架构师",
        "质量工程师",
        "质量保证专员",
        "移动端测试工程师",
        "游戏测试工程师",
        "嵌入式测试工程师",
        "硬件测试工程师",
        "可靠性工程师",
        "认证测试工程师",
        "测试项目经理",
        "用户体验测试工程师",
        "测试数据工程师",
    ),
    "云计算、运维与安全": (
        "运维开发工程师",
        "SRE工程师",
        "云平台工程师",
        "DevOps工程师",
        "网络工程师",
        "系统运维工程师",
        "Linux运维工程师",
        "中间件工程师",
        "容器云工程师",
        "云安全工程师",
        "信息安全工程师",
        "网络安全工程师",
        "渗透测试工程师",
        "安全运营工程师",
        "安全架构师",
        "灾备工程师",
        "IT支持工程师",
    ),
    "产品、项目与解决方案": (
        "产品经理",
        "数据产品经理",
        "AI产品经理",
        "商业产品经理",
        "增长产品经理",
        "用户研究员",
        "项目经理",
        "PMO项目专员",
        "解决方案工程师",
        "售前技术顾问",
        "实施顾问",
        "ERP实施顾问",
        "数字化咨询顾问",
        "IT咨询顾问",
        "业务分析师",
        "需求分析师",
        "产品运营专员",
    ),
    "设计与内容创意": (
        "UI设计师",
        "UX设计师",
        "交互设计师",
        "视觉设计师",
        "平面设计师",
        "品牌设计师",
        "插画师",
        "动画设计师",
        "视频剪辑师",
        "游戏美术设计师",
        "3D设计师",
        "工业设计师",
        "包装设计师",
        "室内设计师",
        "服装设计师",
        "摄影师",
        "内容策划",
    ),
    "市场、品牌与增长": (
        "市场专员",
        "品牌专员",
        "新媒体运营",
        "内容运营",
        "SEO专员",
        "SEM专员",
        "广告投放专员",
        "社交媒体运营",
        "公关专员",
        "活动策划",
        "用户增长专员",
        "市场调研专员",
        "海外市场专员",
        "短视频运营",
        "私域运营",
        "CRM运营专员",
        "直播运营",
    ),
    "运营、电商与客户成功": (
        "电商运营",
        "店铺运营",
        "类目运营",
        "供应链运营",
        "用户运营",
        "社区运营",
        "商家运营",
        "策略运营",
        "平台运营",
        "客服专员",
        "客户成功经理",
        "物流运营",
        "采购专员",
        "订单运营专员",
        "仓储运营专员",
        "风控运营专员",
        "游戏运营",
    ),
    "销售、商务与供应链": (
        "销售代表",
        "大客户销售",
        "客户经理",
        "渠道销售",
        "商务拓展专员",
        "销售运营专员",
        "销售培训师",
        "招商主管",
        "外贸业务员",
        "跨境电商销售",
        "供应链采购经理",
        "供应链计划专员",
        "物流规划专员",
        "采购工程师",
        "招投标专员",
        "合同专员",
        "商务经理",
    ),
    "财务、法务、人力与行政": (
        "财务专员",
        "会计",
        "审计专员",
        "税务专员",
        "出纳",
        "资金专员",
        "法务专员",
        "合规专员",
        "知识产权专员",
        "HRBP",
        "招聘专员",
        "培训专员",
        "绩效专员",
        "薪酬专员",
        "行政专员",
        "总经理助理",
        "人事专员",
    ),
    "机械、电子、制造、能源与生物医药": (
        "机械工程师",
        "结构工程师",
        "电气工程师",
        "电子工程师",
        "硬件工程师",
        "PCB工程师",
        "自动化工程师",
        "控制工程师",
        "工艺工程师",
        "生产工程师",
        "设备工程师",
        "制造质量工程师",
        "研发工程师",
        "生物医药研发专员",
        "临床协调员",
        "医药代表",
        "环保工程师",
    ),
}


FAMILY_DEFAULTS: dict[str, FamilyDefaults] = {
    "软件研发": FamilyDefaults(
        ("软件工程", "程序开发", "开发工程师"),
        ("计算机科学与技术", "软件工程", "网络工程"),
        ("信息管理与信息系统", "数学与应用数学"),
        ("数据结构", "操作系统", "数据库原理", "计算机网络"),
        ("编程基础", "Git", "数据库", "接口开发"),
        ("Python或Java", "SQL", "调试", "代码规范"),
        ("软件测试工程师", "测试开发工程师"),
        ("开发实习生", "软件测试实习生"),
        4,
        ("互联网", "企业服务", "金融科技"),
    ),
    "人工智能与算法": FamilyDefaults(
        ("人工智能", "算法", "机器学习", "AI"),
        ("人工智能", "计算机科学与技术", "数据科学与大数据技术"),
        ("数学与应用数学", "统计学", "电子信息工程"),
        ("线性代数", "概率统计", "机器学习", "Python程序设计"),
        ("Python", "机器学习", "数据处理", "模型评估"),
        ("Python", "NumPy", "Pandas", "基础模型训练"),
        ("数据分析师", "AI应用工程师"),
        ("算法实习生", "数据标注实习生"),
        5,
        ("互联网", "智能制造", "金融科技"),
    ),
    "数据与数据平台": FamilyDefaults(
        ("数据", "大数据", "数据平台", "数仓"),
        ("数据科学与大数据技术", "计算机科学与技术", "统计学"),
        ("数学与应用数学", "信息管理与信息系统", "金融学"),
        ("数据库原理", "统计学", "数据结构", "数据仓库"),
        ("SQL", "Python", "数据建模", "数据质量"),
        ("SQL", "Excel", "Python", "数据可视化"),
        ("数据分析师", "BI分析师"),
        ("数据分析实习生", "数据运营实习生"),
        4,
        ("互联网", "金融科技", "零售电商"),
    ),
    "测试与质量工程": FamilyDefaults(
        ("测试", "质量", "QA", "SDET"),
        ("计算机科学与技术", "软件工程", "电子信息工程"),
        ("网络工程", "自动化", "通信工程"),
        ("软件测试", "数据结构", "操作系统", "数据库原理"),
        ("测试用例设计", "缺陷管理", "接口测试", "沟通协作"),
        ("测试基础", "SQL", "Python", "接口工具"),
        ("软件测试工程师", "质量保证专员"),
        ("测试实习生", "质量实习生"),
        3,
        ("互联网", "智能制造", "企业服务"),
    ),
    "云计算、运维与安全": FamilyDefaults(
        ("云计算", "运维", "安全", "基础设施"),
        ("网络工程", "计算机科学与技术", "信息安全"),
        ("软件工程", "通信工程", "电子信息工程"),
        ("计算机网络", "操作系统", "Linux", "网络安全"),
        ("Linux", "网络基础", "脚本自动化", "故障排查"),
        ("Linux", "Shell", "Docker", "网络基础"),
        ("IT支持工程师", "系统运维工程师"),
        ("运维实习生", "IT支持实习生"),
        4,
        ("云服务", "企业服务", "金融科技"),
    ),
    "产品、项目与解决方案": FamilyDefaults(
        ("产品", "项目", "咨询", "解决方案"),
        ("信息管理与信息系统", "工商管理", "计算机科学与技术"),
        ("市场营销", "工业工程", "电子商务"),
        ("产品设计", "项目管理", "管理学", "用户研究"),
        ("需求分析", "原型设计", "沟通协作", "数据分析"),
        ("Axure或Figma", "Excel", "需求文档", "项目推进"),
        ("产品运营专员", "业务分析师"),
        ("产品实习生", "项目助理"),
        4,
        ("互联网", "企业服务", "智能制造"),
    ),
    "设计与内容创意": FamilyDefaults(
        ("设计", "创意", "内容", "视觉"),
        ("视觉传达设计", "数字媒体艺术", "工业设计"),
        ("新闻学", "广告学", "计算机科学与技术"),
        ("设计基础", "视觉传达", "用户体验", "数字媒体"),
        ("作品集", "视觉表达", "设计工具", "沟通协作"),
        ("Figma", "Photoshop", "作品整理", "审美表达"),
        ("内容策划", "视觉设计师"),
        ("设计实习生", "内容实习生"),
        3,
        ("互联网", "消费品牌", "文化传媒"),
    ),
    "市场、品牌与增长": FamilyDefaults(
        ("市场", "品牌", "增长", "营销"),
        ("市场营销", "广告学", "电子商务"),
        ("新闻学", "工商管理", "国际商务"),
        ("市场营销", "消费者行为学", "传播学", "数据分析"),
        ("内容策划", "数据分析", "用户洞察", "活动执行"),
        ("Excel", "内容写作", "基础投放", "复盘"),
        ("内容运营", "市场专员"),
        ("市场实习生", "新媒体实习生"),
        3,
        ("消费品牌", "互联网", "文化传媒"),
    ),
    "运营、电商与客户成功": FamilyDefaults(
        ("运营", "电商", "客户成功", "用户"),
        ("电子商务", "市场营销", "工商管理"),
        ("物流管理", "国际商务", "信息管理与信息系统"),
        ("运营管理", "电子商务", "数据分析", "客户关系管理"),
        ("用户沟通", "数据分析", "执行推进", "复盘"),
        ("Excel", "内容编辑", "客户沟通", "数据看板"),
        ("客服专员", "订单运营专员"),
        ("运营实习生", "电商实习生"),
        2,
        ("零售电商", "互联网", "物流供应链"),
    ),
    "销售、商务与供应链": FamilyDefaults(
        ("销售", "商务", "供应链", "采购"),
        ("市场营销", "国际商务", "物流管理"),
        ("工商管理", "电子商务", "金融学"),
        ("市场营销", "商务沟通", "供应链管理", "国际贸易"),
        ("客户沟通", "商务谈判", "目标管理", "执行推进"),
        ("Excel", "沟通表达", "客户开发", "合同基础"),
        ("销售代表", "商务拓展专员"),
        ("销售实习生", "商务实习生"),
        2,
        ("消费品牌", "物流供应链", "企业服务"),
    ),
    "财务、法务、人力与行政": FamilyDefaults(
        ("财务", "法务", "人力", "行政"),
        ("会计学", "财务管理", "法学"),
        ("人力资源管理", "工商管理", "金融学"),
        ("会计学", "劳动法", "人力资源管理", "管理学"),
        ("Excel", "专业规范", "文档能力", "沟通协作"),
        ("Excel", "文档处理", "数据核对", "流程意识"),
        ("行政专员", "人事专员"),
        ("财务实习生", "人力实习生"),
        2,
        ("专业服务", "消费品牌", "制造业"),
    ),
    "机械、电子、制造、能源与生物医药": FamilyDefaults(
        ("制造", "硬件", "工程", "医药"),
        ("机械设计制造及其自动化", "电气工程及其自动化", "电子信息工程"),
        ("自动化", "材料科学与工程", "生物工程"),
        ("工程制图", "电路基础", "自动控制原理", "工艺学"),
        ("工程制图", "专业软件", "实验能力", "质量意识"),
        ("CAD", "Excel", "实验记录", "问题分析"),
        ("设备工程师", "质量工程师"),
        ("工程实习生", "制造实习生"),
        4,
        ("智能制造", "新能源", "医药健康"),
    ),
}


ROLE_OVERRIDES: dict[str, dict[str, object]] = {
    "数据工程师": {
        "aliases": ("data engineer", "数据开发工程师", "数仓工程师", "ETL工程师"),
        "required_skills": ("SQL", "Python", "数据建模", "数据仓库", "调度编排"),
        "entry_skills": ("SQL", "Python", "Hive或Spark", "数据质量"),
        "entry_difficulty": 4,
    },
    "数据分析师": {
        "aliases": ("data analyst", "商业分析师", "BI分析"),
        "required_skills": ("SQL", "Excel", "Python", "数据可视化", "业务分析"),
        "entry_skills": ("SQL", "Excel", "Power BI或Tableau", "统计基础"),
        "entry_difficulty": 3,
    },
    "AI Agent工程师": {
        "aliases": ("agent engineer", "ai agent engineer", "智能体工程师", "大模型应用工程师"),
        "required_skills": ("Python", "大模型应用", "提示词工程", "RAG", "接口开发"),
        "entry_skills": ("Python", "API调用", "提示词设计", "简单RAG项目"),
        "entry_difficulty": 4,
    },
    "产品经理": {
        "aliases": ("product manager", "互联网产品经理", "产品专员"),
        "required_skills": ("需求分析", "原型设计", "用户研究", "项目推进", "数据分析"),
        "entry_skills": ("Figma或Axure", "PRD", "竞品分析", "用户访谈"),
        "entry_difficulty": 4,
    },
    "UI设计师": {
        "aliases": ("ui designer", "界面设计师", "视觉界面设计师"),
        "required_skills": ("Figma", "视觉设计", "组件规范", "作品集", "用户体验"),
        "entry_skills": ("Figma", "作品集", "设计规范", "临摹与复盘"),
        "entry_difficulty": 3,
    },
    "财务专员": {
        "aliases": ("finance specialist", "财务助理", "财务会计"),
        "required_skills": ("Excel", "财务核算", "凭证处理", "报表基础", "细致核对"),
        "entry_skills": ("Excel", "会计基础", "财务软件", "凭证整理"),
        "entry_difficulty": 2,
    },
    "数据标注专员": {
        "aliases": ("data annotation", "数据标注", "标注员", "AI数据标注"),
        "required_skills": ("标注规范", "数据质量", "细致核对", "基础工具操作"),
        "entry_skills": ("标注规范", "Excel", "质量检查", "任务管理"),
        "entry_difficulty": 1,
    },
}


def _build_role_seed(family: str, role_name: str) -> RoleSeed:
    defaults = FAMILY_DEFAULTS[family]
    seed = RoleSeed(
        role_name=role_name,
        family=family,
        aliases=(role_name, *defaults.aliases),
        recommended_majors=defaults.recommended_majors,
        adjacent_majors=defaults.adjacent_majors,
        relevant_courses=defaults.relevant_courses,
        required_skills=defaults.required_skills,
        entry_skills=defaults.entry_skills,
        alternative_roles=defaults.alternative_roles,
        internship_roles=defaults.internship_roles,
        entry_difficulty=defaults.entry_difficulty,
        industry_tags=defaults.industry_tags,
        description=f"{family}方向的{role_name}岗位，适合先用可验证的课程、项目或实习成果建立竞争力。",
    )
    changes = ROLE_OVERRIDES.get(role_name)
    return replace(seed, **changes) if changes else seed


ROLE_SEEDS = tuple(
    _build_role_seed(family, role_name)
    for family, role_names in FAMILY_ROLE_NAMES.items()
    for role_name in role_names
)


MAJOR_SEEDS = (
    MajorSeed("计算机科学与技术", "计算机与信息", ("计算机", "CS", "Computer Science"), ("软件研发", "人工智能与算法", "数据与数据平台"), ("编程", "算法", "数据库")),
    MajorSeed("软件工程", "计算机与信息", ("软工", "Software Engineering"), ("软件研发", "测试与质量工程", "云计算、运维与安全"), ("软件工程", "项目协作", "测试")),
    MajorSeed("数据科学与大数据技术", "计算机与信息", ("大数据", "数据科学", "Data Science"), ("数据与数据平台", "人工智能与算法"), ("统计分析", "数据建模", "Python")),
    MajorSeed("人工智能", "计算机与信息", ("AI", "智能科学"), ("人工智能与算法", "软件研发"), ("机器学习", "模型训练", "Python")),
    MajorSeed("网络工程", "计算机与信息", ("网络", "Network Engineering"), ("云计算、运维与安全", "软件研发"), ("网络配置", "Linux", "安全基础")),
    MajorSeed("信息安全", "计算机与信息", ("网络安全", "Cyber Security"), ("云计算、运维与安全", "测试与质量工程"), ("安全基础", "网络", "风险意识")),
    MajorSeed("信息管理与信息系统", "管理与信息", ("信管", "MIS"), ("数据与数据平台", "产品、项目与解决方案", "运营、电商与客户成功"), ("业务分析", "数据分析", "流程设计")),
    MajorSeed("数学与应用数学", "理学", ("数学", "应用数学"), ("人工智能与算法", "数据与数据平台"), ("建模", "统计", "逻辑推理")),
    MajorSeed("统计学", "理学", ("统计", "Statistics"), ("数据与数据平台", "人工智能与算法", "市场、品牌与增长"), ("统计分析", "数据解释", "实验设计")),
    MajorSeed("电子信息工程", "工程技术", ("电子信息", "EE"), ("机械、电子、制造、能源与生物医药", "测试与质量工程", "人工智能与算法"), ("电路", "信号处理", "实验能力")),
    MajorSeed("通信工程", "工程技术", ("通信", "Communications"), ("云计算、运维与安全", "机械、电子、制造、能源与生物医药"), ("通信原理", "网络", "嵌入式")),
    MajorSeed("自动化", "工程技术", ("Automation", "自动控制"), ("机械、电子、制造、能源与生物医药", "测试与质量工程"), ("控制系统", "PLC", "工程实践")),
    MajorSeed("机械设计制造及其自动化", "工程技术", ("机械", "机电"), ("机械、电子、制造、能源与生物医药",), ("制图", "CAD", "工艺")),
    MajorSeed("电气工程及其自动化", "工程技术", ("电气", "电力"), ("机械、电子、制造、能源与生物医药",), ("电路", "控制", "设备调试")),
    MajorSeed("生物工程", "生命科学", ("生物", "Bioengineering"), ("机械、电子、制造、能源与生物医药",), ("实验设计", "质量规范", "数据记录")),
    MajorSeed("临床医学", "生命科学", ("医学", "临床"), ("机械、电子、制造、能源与生物医药",), ("医学基础", "沟通", "规范意识")),
    MajorSeed("药学", "生命科学", ("药剂", "Pharmacy"), ("机械、电子、制造、能源与生物医药",), ("药理", "实验", "合规")),
    MajorSeed("市场营销", "商科", ("营销", "Marketing"), ("市场、品牌与增长", "销售、商务与供应链", "运营、电商与客户成功"), ("市场洞察", "沟通", "活动策划")),
    MajorSeed("电子商务", "商科", ("电商", "E-commerce"), ("运营、电商与客户成功", "市场、品牌与增长", "销售、商务与供应链"), ("平台运营", "数据分析", "商品管理")),
    MajorSeed("工商管理", "商科", ("工商", "Business Administration"), ("产品、项目与解决方案", "运营、电商与客户成功", "销售、商务与供应链"), ("管理", "沟通", "项目推进")),
    MajorSeed("国际商务", "商科", ("国贸", "国际贸易"), ("销售、商务与供应链", "市场、品牌与增长"), ("商务沟通", "贸易", "外语")),
    MajorSeed("物流管理", "商科", ("物流", "供应链"), ("销售、商务与供应链", "运营、电商与客户成功"), ("供应链", "库存", "流程优化")),
    MajorSeed("财务管理", "商科", ("财管", "Finance Management"), ("财务、法务、人力与行政",), ("财务分析", "Excel", "预算")),
    MajorSeed("会计学", "商科", ("会计", "Accounting"), ("财务、法务、人力与行政",), ("核算", "报表", "财务软件")),
    MajorSeed("金融学", "商科", ("金融", "Finance"), ("财务、法务、人力与行政", "数据与数据平台", "销售、商务与供应链"), ("金融基础", "数据分析", "风险意识")),
    MajorSeed("法学", "人文社科", ("法律", "Law"), ("财务、法务、人力与行政",), ("法律检索", "文书", "合规")),
    MajorSeed("人力资源管理", "管理与信息", ("人力", "HR"), ("财务、法务、人力与行政",), ("招聘", "组织", "沟通")),
    MajorSeed("新闻学", "人文社科", ("新闻", "Journalism"), ("设计与内容创意", "市场、品牌与增长"), ("内容写作", "采访", "传播")),
    MajorSeed("广告学", "人文社科", ("广告", "Advertising"), ("市场、品牌与增长", "设计与内容创意"), ("文案", "传播", "创意")),
    MajorSeed("汉语言文学", "人文社科", ("中文", "汉语言"), ("设计与内容创意", "市场、品牌与增长"), ("写作", "内容编辑", "表达")),
    MajorSeed("英语", "人文社科", ("外语", "English"), ("市场、品牌与增长", "销售、商务与供应链"), ("外语沟通", "翻译", "跨文化")),
    MajorSeed("视觉传达设计", "艺术设计", ("视觉设计", "平面设计"), ("设计与内容创意",), ("视觉表达", "版式", "品牌设计")),
    MajorSeed("数字媒体艺术", "艺术设计", ("数媒", "数字媒体"), ("设计与内容创意", "市场、品牌与增长"), ("视频", "交互", "数字内容")),
    MajorSeed("工业设计", "艺术设计", ("产品设计", "Industrial Design"), ("设计与内容创意", "机械、电子、制造、能源与生物医药"), ("产品表达", "建模", "用户研究")),
    MajorSeed("心理学", "人文社科", ("心理", "Psychology"), ("产品、项目与解决方案", "人力资源与行政", "市场、品牌与增长"), ("用户研究", "访谈", "观察")),
    MajorSeed("社会学", "人文社科", ("社会", "Sociology"), ("产品、项目与解决方案", "市场、品牌与增长", "运营、电商与客户成功"), ("调研", "访谈", "数据解释")),
)


def seed_career_catalog(connection: sqlite3.Connection) -> None:
    connection.executemany(
        """
        INSERT INTO role_profile (
            role_name, family, aliases_json, recommended_majors_json, adjacent_majors_json,
            relevant_courses_json, required_skills_json, entry_skills_json,
            alternative_roles_json, internship_roles_json, entry_difficulty,
            industry_tags_json, description
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(role_name) DO UPDATE SET
            family = excluded.family,
            aliases_json = excluded.aliases_json,
            recommended_majors_json = excluded.recommended_majors_json,
            adjacent_majors_json = excluded.adjacent_majors_json,
            relevant_courses_json = excluded.relevant_courses_json,
            required_skills_json = excluded.required_skills_json,
            entry_skills_json = excluded.entry_skills_json,
            alternative_roles_json = excluded.alternative_roles_json,
            internship_roles_json = excluded.internship_roles_json,
            entry_difficulty = excluded.entry_difficulty,
            industry_tags_json = excluded.industry_tags_json,
            description = excluded.description
        """,
        [
            (
                role.role_name,
                role.family,
                _to_json(role.aliases),
                _to_json(role.recommended_majors),
                _to_json(role.adjacent_majors),
                _to_json(role.relevant_courses),
                _to_json(role.required_skills),
                _to_json(role.entry_skills),
                _to_json(role.alternative_roles),
                _to_json(role.internship_roles),
                role.entry_difficulty,
                _to_json(role.industry_tags),
                role.description,
            )
            for role in ROLE_SEEDS
        ],
    )
    connection.executemany(
        """
        INSERT INTO major_catalog (
            major_name, category, aliases_json, related_families_json, transferable_skills_json
        ) VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(major_name) DO UPDATE SET
            category = excluded.category,
            aliases_json = excluded.aliases_json,
            related_families_json = excluded.related_families_json,
            transferable_skills_json = excluded.transferable_skills_json
        """,
        [
            (
                major.major_name,
                major.category,
                _to_json(major.aliases),
                _to_json(major.related_families),
                _to_json(major.transferable_skills),
            )
            for major in MAJOR_SEEDS
        ],
    )


def _to_json(values: tuple[str, ...]) -> str:
    return json.dumps(values, ensure_ascii=False)


assert len(ROLE_FAMILIES) == 12
assert len(ROLE_SEEDS) == 204
