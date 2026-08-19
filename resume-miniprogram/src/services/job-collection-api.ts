import { request } from "./http"

export type FavoriteJob = {
  id: string
  roleName: string
  note: string
  createdAt: string
}

type BackendFavoriteJob = {
  id: string
  role_name: string
  note: string
  created_at: string
}

type BackendJobMatchSubscription = {
  enabled: boolean
  match_filter: string
  last_notify_at: string | null
}

export type JobMatchSubscription = {
  enabled: boolean
  matchFilter: string
  lastNotifyAt: string | null
}

function mapFavorite(item: BackendFavoriteJob): FavoriteJob {
  return { id: item.id, roleName: item.role_name, note: item.note, createdAt: item.created_at }
}

export async function listFavoriteJobs(): Promise<FavoriteJob[]> {
  const data = await request<{ items: BackendFavoriteJob[] }>("/api/job-collection/favorites")
  return data.items.map(mapFavorite)
}

export async function saveFavoriteJob(roleName: string, note = ""): Promise<FavoriteJob> {
  return mapFavorite(await request<BackendFavoriteJob>("/api/job-collection/favorites", "POST", {
    role_name: roleName,
    note,
  }))
}

export async function deleteFavoriteJob(id: string): Promise<void> {
  await request<{ id: string }>(`/api/job-collection/favorites/${encodeURIComponent(id)}`, "DELETE")
}

export async function getJobMatchSubscription(): Promise<boolean> {
  return (await getJobMatchSubscriptionSettings()).enabled
}

export async function setJobMatchSubscription(enabled: boolean): Promise<boolean> {
  return (await setJobMatchSubscriptionSettings(enabled)).enabled
}

function mapSubscription(item: BackendJobMatchSubscription): JobMatchSubscription {
  return { enabled: item.enabled, matchFilter: item.match_filter, lastNotifyAt: item.last_notify_at }
}

export async function getJobMatchSubscriptionSettings(): Promise<JobMatchSubscription> {
  return mapSubscription(await request<BackendJobMatchSubscription>("/api/job-collection/subscription"))
}

export async function setJobMatchSubscriptionSettings(enabled: boolean, matchFilter?: string): Promise<JobMatchSubscription> {
  const data: { enabled: boolean; match_filter?: string } = { enabled }
  if (matchFilter !== undefined) data.match_filter = matchFilter
  return mapSubscription(await request<BackendJobMatchSubscription>("/api/job-collection/subscription", "PUT", data))
}
