import { request } from "./http"

export interface BackendExportResult {
  filename: string
  download_url: string
  expires_at: string
}

export interface ExportResult {
  filename: string
  downloadUrl: string
  expiresAt: string
}

async function requestExport(path: string, clientId: string, draftId: string): Promise<ExportResult> {
  const result = await request<BackendExportResult>(path, "POST", {
    client_id: clientId,
    draft_id: draftId,
  })
  return {
    filename: result.filename,
    downloadUrl: result.download_url,
    expiresAt: result.expires_at,
  }
}

export function requestWordExport(clientId: string, draftId: string): Promise<ExportResult> {
  return requestExport("/api/export/word", clientId, draftId)
}

export function requestPdfExport(clientId: string, draftId: string): Promise<ExportResult> {
  return requestExport("/api/export/pdf", clientId, draftId)
}
