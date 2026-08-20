import { apiUrl, toUserMessage } from "./http"
import { getAuthToken } from "../stores/session"
import type { ResumePayload } from "../types/resume"

type BackendResumePreview = {
  version: 1
  basic: { name: string; phone: string; email: string; city: string }
  job: { target_role: string; employment_type: string; expected_salary: string }
  education: Array<{ school: string; major?: string; degree?: string; start_date?: string; end_date?: string; courses?: string }>
  employment: Array<{ company: string; position?: string; start_date?: string; end_date?: string; description?: string }>
  projects: Array<{ name: string; role?: string; start_date?: string; end_date?: string; description?: string }>
  skills: { skills: string[]; certificates: string[] }
  self_evaluation: string
  section_visibility: { basic: boolean; job: boolean; education: boolean; employment: boolean; projects: boolean; skills: boolean; self_evaluation: boolean }
}

type BackendImportResult = {
  id: string
  status: string
  original_filename: string
  parsed_resume: BackendResumePreview
}

export type ResumeImportResult = {
  id: string
  status: string
  originalFilename: string
  parsedResume: ResumePayload
}

type UniUploadFile = (options: {
  url: string
  filePath: string
  name: string
  header?: Record<string, string>
  success: (response: { statusCode: number; data: string }) => void
  fail: (reason: unknown) => void
}) => void

export function mapResumeImportPreview(preview: BackendResumePreview): ResumePayload {
  return {
    version: 1,
    basic: { ...preview.basic, gender: "" },
    job: {
      targetRole: preview.job.target_role,
      availability: preview.job.employment_type,
      expectedSalary: preview.job.expected_salary,
    },
    education: preview.education.map((item) => ({
      school: item.school, major: item.major || "", degree: item.degree || "",
      startDate: item.start_date || "", endDate: item.end_date || "", courses: item.courses || "",
    })),
    employment: preview.employment.map((item) => ({
      company: item.company, position: item.position || "", startDate: item.start_date || "",
      endDate: item.end_date || "", description: item.description || "",
    })),
    projects: preview.projects.map((item) => ({
      name: item.name, role: item.role || "", startDate: item.start_date || "",
      endDate: item.end_date || "", description: item.description || "",
    })),
    skills: { skills: preview.skills.skills, certificates: preview.skills.certificates, englishLevel: "" },
    selfEvaluation: preview.self_evaluation,
    sectionVisibility: {
      basic: preview.section_visibility.basic, job: preview.section_visibility.job,
      education: preview.section_visibility.education, employment: preview.section_visibility.employment,
      projects: preview.section_visibility.projects, skills: preview.section_visibility.skills,
      selfEvaluation: preview.section_visibility.self_evaluation,
    },
  }
}

export async function uploadResumeImport(draftId: string, filePath: string): Promise<ResumeImportResult> {
  const uploadFile = (globalThis as typeof globalThis & { uni?: { uploadFile?: UniUploadFile } }).uni?.uploadFile
  if (!uploadFile) throw new Error("当前运行环境不支持文件上传")
  return new Promise((resolve, reject) => {
    uploadFile({
      url: apiUrl(`/api/draft/${encodeURIComponent(draftId)}/imports`),
      filePath,
      name: "file",
      header: getAuthToken() ? { Authorization: `Bearer ${getAuthToken()}` } : {},
      success: (response) => {
        try {
          const envelope = JSON.parse(response.data) as { code?: string; message?: string; data?: BackendImportResult }
          if (response.statusCode >= 400 || envelope.code !== "ok" || !envelope.data) {
            throw new Error(toUserMessage(envelope.message, "简历文件上传失败，请检查格式后重试。"))
          }
          resolve({
            id: envelope.data.id,
            status: envelope.data.status,
            originalFilename: envelope.data.original_filename,
            parsedResume: mapResumeImportPreview(envelope.data.parsed_resume),
          })
        } catch (reason) {
          reject(reason instanceof Error ? reason : new Error("简历文件上传失败，请稍后重试。"))
        }
      },
      fail: (reason) => reject(new Error(toUserMessage(reason, "简历文件上传失败，请稍后重试。"))),
    })
  })
}
