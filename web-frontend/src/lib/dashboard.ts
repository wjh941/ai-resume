import { readItems, requestApi } from "./api"

type Requester = <T>(path: string, init?: RequestInit) => Promise<T>

type ItemsResponse = Array<{ id: string; status?: string }> | { items?: Array<{ id: string; status?: string }> }

type DraftListResponse = Array<{ id: string }> | { items?: Array<{ id: string }> }

export type OverviewState = {
  applicationCount: number
  draftCount: number
  openTaskCount: number
}

export async function loadOverview(
  request: Requester = requestApi,
  planId = "web-workspace",
): Promise<OverviewState> {
  const [applications, drafts, tasks] = await Promise.all([
    request<ItemsResponse>("/api/applications"),
    request<DraftListResponse>("/api/draft/list"),
    request<ItemsResponse>(`/api/career/tasks?plan_id=${encodeURIComponent(planId)}`),
  ])

  return {
    applicationCount: readItems(applications).length,
    draftCount: readItems(drafts).length,
    openTaskCount: readItems(tasks).filter((task) => task.status !== "completed").length,
  }
}
