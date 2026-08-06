import { request } from "./http"
import type { JobConsultation, ResumeReview } from "../types/consultation"
import type { JobIntelligence, ResumeDraft, ResumePayload } from "../types/resume"

type BackendJob = {
  version: 1; role_name: string; salary_by_experience: Record<string, string>
  responsibilities: string[]; hard_requirements: string[]; required_skills: string[]
  bonus_skills: string[]; career_route: string[]
}

type BackendConsultationSection = {
  order: number; title: string; items: string[]
}

type BackendJobConsultation = {
  identity_code: JobConsultation["identityCode"]; identity_label: string
  job_intelligence: BackendJob
  job_analysis_sections: BackendConsultationSection[]
  identity_plan: { title: string; sections: BackendConsultationSection[] }
  follow_up_question: string
}

type BackendResumeReview = {
  identity_code: ResumeReview["identityCode"]; identity_label: string
  issues: string[]; rewrite_examples: string[]; keywords: string[]
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

export async function queryJobConsultation(
  roleName: string,
  identityCode: JobConsultation["identityCode"],
): Promise<JobConsultation> {
  const response = await request<BackendJobConsultation>("/api/consultation/job-analysis", "POST", {
    role_name: roleName,
    identity_code: identityCode,
  })
  return {
    identityCode: response.identity_code,
    identityLabel: response.identity_label,
    jobIntelligence: fromBackendJob(response.job_intelligence),
    jobAnalysisSections: response.job_analysis_sections,
    identityPlan: response.identity_plan,
    followUpQuestion: response.follow_up_question,
  }
}

export async function reviewResumeText(
  resumeText: string,
  identityCode: ResumeReview["identityCode"],
  roleName?: string,
): Promise<ResumeReview> {
  const response = await request<BackendResumeReview>("/api/consultation/resume-review", "POST", {
    resume_text: resumeText,
    identity_code: identityCode,
    role_name: roleName || undefined,
  })
  return {
    identityCode: response.identity_code,
    identityLabel: response.identity_label,
    issues: response.issues,
    rewriteExamples: response.rewrite_examples,
    keywords: response.keywords,
  }
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
