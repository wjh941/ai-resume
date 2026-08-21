import { request } from "./http"
import type { LocalJobMatchItem, LocalJobMatchResult } from "../types/job-match"

type BackendJobMatchItem = {
  role_name: string
  company: string
  city: string
  salary_range: string
  category: string
  match_score: number
  match_score_reference?: number | null
  responsibilities: string[]
  requirements: string[]
}

function mapItem(item: BackendJobMatchItem): LocalJobMatchItem {
  return {
    roleName: item.role_name,
    company: item.company,
    city: item.city,
    salaryRange: item.salary_range,
    category: item.category,
    matchScore: item.match_score,
    matchScoreReference: item.match_score_reference ?? null,
    responsibilities: item.responsibilities,
    requirements: item.requirements,
  }
}

export async function listLocalJobMatches(targetRole: string): Promise<LocalJobMatchResult> {
  const data = await request<{ items: BackendJobMatchItem[]; source_notice: string }>(
    "/api/job/match",
    "POST",
    { target_role: targetRole },
  )
  return { items: data.items.map(mapItem), sourceNotice: data.source_notice }
}
