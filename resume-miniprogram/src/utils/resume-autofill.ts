import type { JobIntelligence, ResumeDraft } from "../types/resume"

function firstSalaryRange(job: JobIntelligence): string {
  return job.salaryByExperience["1-3_years"] || Object.values(job.salaryByExperience).find(Boolean) || ""
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

  if (!draft.resume.selfEvaluation.trim()) {
    draft.resume.selfEvaluation = `目标岗位：${job.roleName}。正在根据岗位要求完善简历，建议重点确认：${job.requiredSkills.join("、")}。`
  }
}
