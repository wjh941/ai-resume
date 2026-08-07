import type { JobIntelligence, ResumeDraft, ResumePayload } from "../types/resume"

type ProjectDraft = ResumePayload["projects"][number]
type EmploymentDraft = ResumePayload["employment"][number]

const UNKNOWN = "[待确认]"

function firstSalaryRange(job: JobIntelligence): string {
  return job.salaryByExperience["1-3_years"] || Object.values(job.salaryByExperience).find(Boolean) || ""
}

function relevantSkills(job: JobIntelligence): string[] {
  return [...job.requiredSkills, ...job.bonusSkills].filter(Boolean).slice(0, 4)
}

function roleSkillText(job: JobIntelligence): string {
  return relevantSkills(job).join("、") || `${job.roleName}核心技能`
}

function roleResponsibility(job: JobIntelligence): string {
  return job.responsibilities[0] || `围绕${job.roleName}完成可验证交付`
}

export function createRoleBasedProjectDraft(job: JobIntelligence): ProjectDraft {
  const skills = roleSkillText(job)
  return {
    name: `${job.roleName}岗位实战项目 ${UNKNOWN}`,
    role: `项目负责人 / 核心成员 ${UNKNOWN}`,
    startDate: UNKNOWN,
    endDate: UNKNOWN,
    description: [
      `业务场景：围绕${UNKNOWN}真实业务场景，拆解与${job.roleName}相关的问题、目标用户和验收标准。`,
      `职责与行动：基于本人实际完成的内容，使用${skills}完成${roleResponsibility(job)}，并记录方案取舍与协作过程。`,
      `交付物：沉淀${UNKNOWN}数据/代码/原型/报告/复盘材料，确保可在面试中展示具体过程和个人贡献边界。`,
      `结果与证据：将真实可核验成果填写为${UNKNOWN}；无准确数据时保留占位符，不编造效率、金额或比例。`,
    ].join("\n"),
  }
}

export function createRoleBasedProjectDrafts(job: JobIntelligence): ProjectDraft[] {
  const skills = roleSkillText(job)
  return [
    createRoleBasedProjectDraft(job),
    {
      name: `${job.roleName}业务质量与交付项目 ${UNKNOWN}`,
      role: `执行成员 / 质量协同 ${UNKNOWN}`,
      startDate: UNKNOWN,
      endDate: UNKNOWN,
      description: [
        `业务场景：针对${UNKNOWN}真实业务流程中的质量、效率或协作问题，明确问题边界和相关干系人。`,
        `职责与行动：在本人真实参与范围内，使用${skills}完成数据核查、方案执行、问题跟进或结果复盘。`,
        `交付物：输出${UNKNOWN}检查清单/分析报告/操作说明/项目复盘，并补充本人实际负责的具体模块。`,
        `结果与证据：仅填写本人可提供的真实反馈、作品链接或可复核结果${UNKNOWN}，未确认数据不得量化。`,
      ].join("\n"),
    },
  ]
}

export function createRoleBasedInternshipDraft(job: JobIntelligence): EmploymentDraft {
  const skills = roleSkillText(job)
  return {
    company: `${UNKNOWN}真实公司`,
    position: `${job.roleName}实习生 ${UNKNOWN}`,
    startDate: UNKNOWN,
    endDate: UNKNOWN,
    description: [
      `工作场景：在${UNKNOWN}真实团队/业务线中，参与与${job.roleName}相关的日常任务和项目推进。`,
      `具体贡献：基于本人实际完成情况，使用${skills}协助处理${roleResponsibility(job)}，明确自己负责的模块。`,
      `协作与交付：与${UNKNOWN}角色同步需求、风险和进度，输出${UNKNOWN}可复核材料。`,
      `成果证据：补充真实的结果、反馈或作品链接${UNKNOWN}；未确认的数据不得写成量化成果。`,
    ].join("\n"),
  }
}

export function prepareResumeForJob(draft: ResumeDraft, job: JobIntelligence): void {
  draft.jobIntelligence = job

  if (!draft.jobTitle.trim()) draft.jobTitle = job.roleName
  if (!draft.resume.job.targetRole.trim()) draft.resume.job.targetRole = job.roleName
  if (!draft.resume.job.expectedSalary.trim()) draft.resume.job.expectedSalary = firstSalaryRange(job)
  if (!draft.resume.job.availability.trim()) draft.resume.job.availability = "可协商"

  if (draft.resume.skills.skills.length === 0) {
    draft.resume.skills.skills = job.requiredSkills.map((skill) => `${skill}（待确认）`)
  }

  if (draft.resume.projects.length === 0) {
    draft.resume.projects.push(...createRoleBasedProjectDrafts(job))
  }

  if (draft.resume.employment.length === 0) {
    draft.resume.employment.push(createRoleBasedInternshipDraft(job))
  }

  if (!draft.resume.selfEvaluation.trim()) {
    draft.resume.selfEvaluation = [
      `目标岗位：${job.roleName}。`,
      `已根据岗位要求整理需要确认的技能：${job.requiredSkills.join("、")}。`,
      "优先补充本人真实完成的项目场景、职责边界、交付物和可核验证据；未确认数据统一保留 [待确认]。",
    ].join("")
  }
}
