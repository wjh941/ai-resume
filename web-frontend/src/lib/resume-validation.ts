import type { DraftRecord } from "./drafts"

const PHONE_PATTERN = /^1\d{10}$/
const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

export function validateDraft(draft: DraftRecord): Record<string, string> {
  const errors: Record<string, string> = {}
  if (!draft.jobTitle.trim()) errors.jobTitle = "请填写草稿名称"
  if (!draft.resume.basic.name.trim()) errors["basic.name"] = "请填写姓名"
  if (!PHONE_PATTERN.test(draft.resume.basic.phone.trim())) errors["basic.phone"] = "请输入有效的手机号码"
  if (!EMAIL_PATTERN.test(draft.resume.basic.email.trim())) errors["basic.email"] = "请输入有效的邮箱地址"
  if (!draft.resume.job.targetRole.trim()) errors["job.targetRole"] = "请填写期望岗位"
  return errors
}
