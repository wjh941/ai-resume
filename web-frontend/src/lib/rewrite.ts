import { requestApi, SLOW_REQUEST_TIMEOUT_MS } from "./api"
import { ApiRequestError } from "./api"
import type { ResumePayload } from "./drafts"

export type RewriteMode = "light" | "deep"

export const REWRITE_INSTRUCTIONS_MAX = 200

export type RewriteDiffEntry = {
  kind: "employment" | "projects" | "self"
  index: number
  title: string
  before: string
  after: string
}

function normalizeRoleName(roleName: string): string {
  return roleName.trim() || "目标岗位"
}

/**
 * AI 按需改写：把当前简历、目标岗位、模式和用户自定义要求交给
 * /api/resume/ai-rewrite；后端事实守卫保证不引入原文没有的事实。
 */
export async function aiRewriteResume(input: {
  resume: ResumePayload
  roleName: string
  mode: RewriteMode
  instructions?: string
}): Promise<ResumePayload> {
  const payload = await requestApi<Record<string, unknown>>(
    "/api/resume/ai-rewrite",
    {
      method: "POST",
      body: JSON.stringify({
        resume: {
          version: 1,
          basic: input.resume.basic,
          job: {
            target_role: input.resume.job.targetRole,
            expected_salary: input.resume.job.expectedSalary,
            employment_type: input.resume.job.employmentType,
          },
          education: input.resume.education.map((item) => ({
            school: item.school, major: item.major, degree: item.degree,
            start_date: item.startDate, end_date: item.endDate,
          })),
          employment: input.resume.employment.map((item) => ({
            company: item.company, position: item.position,
            start_date: item.startDate, end_date: item.endDate, description: item.description,
          })),
          projects: input.resume.projects.map((item) => ({
            name: item.name, role: item.role,
            start_date: item.startDate, end_date: item.endDate, description: item.description,
          })),
          skills: { skills: input.resume.skills.skills, certificates: input.resume.skills.certificates },
          self_evaluation: input.resume.selfEvaluation,
          section_visibility: {
            basic: input.resume.sectionVisibility.basic,
            job: input.resume.sectionVisibility.job,
            education: input.resume.sectionVisibility.education,
            employment: input.resume.sectionVisibility.employment,
            projects: input.resume.sectionVisibility.projects,
            skills: input.resume.sectionVisibility.skills,
            self_evaluation: input.resume.sectionVisibility.selfEvaluation,
          },
        },
        job: { version: 1, role_name: normalizeRoleName(input.roleName || input.resume.job.targetRole), required_skills: [] },
        mode: input.mode,
        instructions: input.instructions?.trim() ? input.instructions.trim() : null,
      }),
    },
    { timeoutMs: SLOW_REQUEST_TIMEOUT_MS },
  )
  return parseRewrittenResume(payload)
}

function parseRewrittenResume(payload: Record<string, unknown>): ResumePayload {
  const basic = payload.basic as Record<string, string> | undefined
  const job = payload.job as Record<string, string> | undefined
  if (!basic || !job) throw new ApiRequestError("AI 改写返回内容不完整，请稍后重试", 0, "ai_invalid_response")
  const visibility = (payload.section_visibility ?? {}) as Record<string, boolean>
  return {
    version: 1,
    basic: { name: basic.name ?? "", phone: basic.phone ?? "", email: basic.email ?? "", city: basic.city ?? "" },
    job: {
      targetRole: job.target_role ?? "",
      expectedSalary: job.expected_salary ?? "",
      employmentType: job.employment_type ?? "",
    },
    education: (payload.education as Array<Record<string, string>> | undefined)?.map((item) => ({
      school: item.school ?? "", major: item.major ?? "", degree: item.degree ?? "",
      startDate: item.start_date ?? "", endDate: item.end_date ?? "",
    })) ?? [],
    employment: (payload.employment as Array<Record<string, string>> | undefined)?.map((item) => ({
      company: item.company ?? "", position: item.position ?? "",
      startDate: item.start_date ?? "", endDate: item.end_date ?? "", description: item.description ?? "",
    })) ?? [],
    projects: (payload.projects as Array<Record<string, string>> | undefined)?.map((item) => ({
      name: item.name ?? "", role: item.role ?? "",
      startDate: item.start_date ?? "", endDate: item.end_date ?? "", description: item.description ?? "",
    })) ?? [],
    skills: {
      skills: (payload.skills as { skills?: string[] } | undefined)?.skills ?? [],
      certificates: (payload.skills as { certificates?: string[] } | undefined)?.certificates ?? [],
    },
    selfEvaluation: (payload.self_evaluation as string | undefined) ?? "",
    sectionVisibility: {
      basic: visibility.basic ?? true,
      job: visibility.job ?? true,
      education: visibility.education ?? true,
      employment: visibility.employment ?? true,
      projects: visibility.projects ?? true,
      skills: visibility.skills ?? true,
      selfEvaluation: visibility.self_evaluation ?? true,
    },
  }
}

/** 逐字段 diff：只列出确实变化了描述性文案的条目，供改写预览。 */
export function computeRewriteDiff(before: ResumePayload, after: ResumePayload): RewriteDiffEntry[] {
  const entries: RewriteDiffEntry[] = []
  after.employment.forEach((item, index) => {
    const old = before.employment[index]
    if (!old || old.description !== item.description) {
      entries.push({
        kind: "employment", index,
        title: [item.company, item.position].filter(Boolean).join(" · ") || `工作经历 ${index + 1}`,
        before: old?.description ?? "", after: item.description,
      })
    }
  })
  after.projects.forEach((item, index) => {
    const old = before.projects[index]
    if (!old || old.description !== item.description) {
      entries.push({
        kind: "projects", index,
        title: item.name || `项目 ${index + 1}`,
        before: old?.description ?? "", after: item.description,
      })
    }
  })
  if (before.selfEvaluation !== after.selfEvaluation) {
    entries.push({ kind: "self", index: 0, title: "自我评价", before: before.selfEvaluation, after: after.selfEvaluation })
  }
  return entries
}
