import { request } from "./http"
import type { JobIntelligence, ResumeDraft, ResumePayload } from "../types/resume"

type BackendJob = {
  version: 1; role_name: string; salary_by_experience: Record<string, string>
  responsibilities: string[]; hard_requirements: string[]; required_skills: string[]
  bonus_skills: string[]; career_route: string[]
}

function fromBackendJob(job: BackendJob): JobIntelligence {
  return {
    version: job.version, roleName: job.role_name, salaryByExperience: job.salary_by_experience,
    responsibilities: job.responsibilities, hardRequirements: job.hard_requirements,
    requiredSkills: job.required_skills, bonusSkills: job.bonus_skills, careerRoute: job.career_route,
  }
}

function toBackendResume(resume: ResumePayload) {
  return {
    version: 1,
    basic: resume.basic,
    job: { target_role: resume.job.targetRole, employment_type: resume.job.availability, expected_salary: resume.job.expectedSalary },
    education: resume.education.map((item) => ({
      school: item.school, major: item.major, degree: item.degree,
      start_date: item.startDate, end_date: item.endDate, courses: item.courses,
    })),
    employment: resume.employment.map((item) => ({
      company: item.company, position: item.position, start_date: item.startDate,
      end_date: item.endDate, description: item.description,
    })),
    projects: resume.projects.map((item) => ({
      name: item.name, role: item.role, start_date: item.startDate,
      end_date: item.endDate, description: item.description,
    })),
    skills: resume.skills,
    self_evaluation: resume.selfEvaluation,
    section_visibility: {
      basic: resume.sectionVisibility.basic, job: resume.sectionVisibility.job,
      education: resume.sectionVisibility.education, employment: resume.sectionVisibility.employment,
      projects: resume.sectionVisibility.projects, skills: resume.sectionVisibility.skills,
      self_evaluation: resume.sectionVisibility.selfEvaluation,
    },
  }
}

export async function queryJob(roleName: string): Promise<JobIntelligence> {
  return fromBackendJob(await request<BackendJob>("/api/job/query", "POST", { role_name: roleName }))
}

export async function saveDraft(clientId: string, draft: ResumeDraft): Promise<{ id: string }> {
  return request("/api/draft/save", "POST", {
    id: draft.id, client_id: clientId, job_title: draft.jobTitle || draft.resume.job.targetRole,
    template_id: draft.templateId, resume: toBackendResume(draft.resume),
    job_intelligence: draft.jobIntelligence && {
      version: 1, role_name: draft.jobIntelligence.roleName,
      salary_by_experience: draft.jobIntelligence.salaryByExperience,
      responsibilities: draft.jobIntelligence.responsibilities,
      hard_requirements: draft.jobIntelligence.hardRequirements,
      required_skills: draft.jobIntelligence.requiredSkills,
      bonus_skills: draft.jobIntelligence.bonusSkills, career_route: draft.jobIntelligence.careerRoute,
    },
  })
}
