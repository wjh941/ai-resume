import { request } from "./http"

export type OperatorKnowledgeItem = {
  id: string
  title: string
  content: string
  status: "active" | "offline" | "invalid"
  version: number
  createdAt: string
  updatedAt: string
}

export type OperatorKnowledgeVersion = Omit<OperatorKnowledgeItem, "id" | "version" | "updatedAt"> & { version: number }

type BackendKnowledgeItem = {
  id: string
  title: string
  content: string
  status: OperatorKnowledgeItem["status"]
  version: number
  created_at: string
  updated_at: string
}

function mapItem(item: BackendKnowledgeItem): OperatorKnowledgeItem {
  return {
    id: item.id, title: item.title, content: item.content, status: item.status,
    version: item.version, createdAt: item.created_at, updatedAt: item.updated_at,
  }
}

export async function listOperatorKnowledge(): Promise<OperatorKnowledgeItem[]> {
  const data = await request<{ items: BackendKnowledgeItem[] }>("/api/operator/knowledge-items")
  return data.items.map(mapItem)
}

export async function createOperatorKnowledge(payload: Pick<OperatorKnowledgeItem, "title" | "content" | "status">): Promise<OperatorKnowledgeItem> {
  return mapItem(await request<BackendKnowledgeItem>("/api/operator/knowledge-items", "POST", payload))
}

export async function updateOperatorKnowledge(
  id: string,
  payload: Partial<Pick<OperatorKnowledgeItem, "title" | "content" | "status">>,
): Promise<OperatorKnowledgeItem> {
  return mapItem(await request<BackendKnowledgeItem>(`/api/operator/knowledge-items/${encodeURIComponent(id)}`, "PATCH", payload))
}

export async function listOperatorKnowledgeVersions(id: string): Promise<OperatorKnowledgeVersion[]> {
  const data = await request<{ items: Array<{ version: number; title: string; content: string; status: OperatorKnowledgeItem["status"]; created_at: string }> }>(
    `/api/operator/knowledge-items/${encodeURIComponent(id)}/versions`,
  )
  return data.items.map((item) => ({
    title: item.title, content: item.content, status: item.status, version: item.version, createdAt: item.created_at,
  }))
}

export async function restoreOperatorKnowledgeVersion(id: string, version: number): Promise<OperatorKnowledgeItem> {
  return mapItem(await request<BackendKnowledgeItem>(
    `/api/operator/knowledge-items/${encodeURIComponent(id)}/versions/${version}/restore`, "POST",
  ))
}
