import { request } from "./http"
import type { KnowledgeSource, KnowledgeSyncSummary } from "../types/knowledge-sync"

type BackendSource = {
  source_key: string
  display_name: string
  direct_url: string | null
  allowed_hosts: string[]
  file_format: KnowledgeSource["fileFormat"]
  parser_kind: KnowledgeSource["parserKind"]
  enabled: boolean
  disabled_reason: string | null
}

type BackendSummary = {
  run_id: number
  mode: KnowledgeSyncSummary["mode"]
  status: KnowledgeSyncSummary["status"]
  added_roles: number
  added_majors: number
  skipped_rows: number
  errors: string[]
}

function toSource(source: BackendSource): KnowledgeSource {
  return {
    sourceKey: source.source_key,
    displayName: source.display_name,
    directUrl: source.direct_url,
    allowedHosts: source.allowed_hosts,
    fileFormat: source.file_format,
    parserKind: source.parser_kind,
    enabled: source.enabled,
    disabledReason: source.disabled_reason,
  }
}

function toSummary(summary: BackendSummary): KnowledgeSyncSummary {
  return {
    runId: summary.run_id,
    mode: summary.mode,
    status: summary.status,
    addedRoles: summary.added_roles,
    addedMajors: summary.added_majors,
    skippedRows: summary.skipped_rows,
    errors: summary.errors,
  }
}

export async function listKnowledgeSources(): Promise<KnowledgeSource[]> {
  const data = await request<{ items: BackendSource[] }>("/api/knowledgebase/sources")
  return data.items.map(toSource)
}

export async function startOfficialKnowledgeSync(): Promise<KnowledgeSyncSummary> {
  return toSummary(await request<BackendSummary>("/api/knowledgebase/sync/official", "POST"))
}
