import { requestApi } from "./api"

type Requester = <T>(path: string, init?: RequestInit) => Promise<T>

type ItemsResponse = {
  items: Array<{ id: string; status?: string }>
}

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
    request<ItemsResponse>("/api/draft/list"),
    request<ItemsResponse>(`/api/career/tasks?plan_id=${encodeURIComponent(planId)}`),
  ])

  return {
    applicationCount: applications.items.length,
    draftCount: drafts.items.length,
    openTaskCount: tasks.items.filter((task) => task.status !== "completed").length,
  }
}
