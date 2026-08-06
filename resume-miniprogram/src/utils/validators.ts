import type { ResumePayload } from "../types/resume"

export interface ValidationError {
  field: string
  message: string
}

const PHONE_PATTERN = /^1\d{10}$/
const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

export function validateResume(resume: ResumePayload): ValidationError[] {
  const errors: ValidationError[] = []
  if (!resume.basic.name.trim()) errors.push({ field: "basic.name", message: "请填写姓名" })
  if (!PHONE_PATTERN.test(resume.basic.phone.trim())) {
    errors.push({ field: "basic.phone", message: "请输入有效的手机号码" })
  }
  if (!EMAIL_PATTERN.test(resume.basic.email.trim())) {
    errors.push({ field: "basic.email", message: "请输入有效的邮箱地址" })
  }
  if (!resume.job.targetRole.trim()) errors.push({ field: "job.targetRole", message: "请填写期望岗位" })
  return errors
}
