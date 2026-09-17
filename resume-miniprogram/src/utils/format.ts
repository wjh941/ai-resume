const pad = (value: number): string => String(value).padStart(2, "0")

/** 把 ISO8601 字符串拆成日期选择器可用的 { date, time }；空值或解析失败返回空日期与默认时间。 */
export function splitIsoDateTime(value: string | null | undefined): { date: string; time: string } {
  if (!value) return { date: "", time: "09:00" }
  const parsed = new Date(value)
  if (!Number.isFinite(parsed.getTime())) return { date: "", time: "09:00" }
  return {
    date: `${parsed.getFullYear()}-${pad(parsed.getMonth() + 1)}-${pad(parsed.getDate())}`,
    time: `${pad(parsed.getHours())}:${pad(parsed.getMinutes())}`,
  }
}

/** 组合日期与时间(本地 +08:00)为后端可解析的 ISO8601 字符串。 */
export function toIsoDateTime(date: string, time: string): string {
  return `${date}T${time}:00+08:00`
}

export function todayIsoDate(): string {
  const now = new Date()
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`
}

/** ISO8601 → "YYYY-MM-DD HH:mm"；空值返回 fallback，解析失败保留原文。 */
export function formatDateTime(value: string | null | undefined, fallback = ""): string {
  if (!value) return fallback
  const parsed = new Date(value)
  if (!Number.isFinite(parsed.getTime())) return value
  return `${parsed.getFullYear()}-${pad(parsed.getMonth() + 1)}-${pad(parsed.getDate())} ${pad(parsed.getHours())}:${pad(parsed.getMinutes())}`
}
