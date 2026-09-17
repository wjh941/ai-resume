const pad = (value: number): string => String(value).padStart(2, "0")

/** ISO8601 → "YYYY-MM-DD HH:mm"（本地时区）；空值返回 fallback，解析失败保留原文。 */
export function formatDateTime(value: string | null | undefined, fallback = ""): string {
  if (!value) return fallback
  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) return value
  return `${parsed.getFullYear()}-${pad(parsed.getMonth() + 1)}-${pad(parsed.getDate())} ${pad(parsed.getHours())}:${pad(parsed.getMinutes())}`
}

const TEMPLATE_LABELS: Record<string, string> = {
  business: "商务模板",
  technology: "技术模板",
  graduate: "毕业生模板",
  analytics: "分析模板",
}

/** 模板枚举 → 中文名；未知值保留原文，空值返回 fallback。 */
export function templateLabel(templateId: string | null | undefined, fallback = "默认模板"): string {
  if (!templateId) return fallback
  return TEMPLATE_LABELS[templateId] ?? templateId
}
