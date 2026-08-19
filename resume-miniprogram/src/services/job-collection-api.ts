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
  return (await request<{ enabled: boolean }>("/api/job-collection/subscription")).enabled
}

export async function setJobMatchSubscription(enabled: boolean): Promise<boolean> {
  return (await request<{ enabled: boolean }>("/api/job-collection/subscription", "PUT", { enabled })).enabled
}
