export type KnowledgeSource = {
  sourceKey: string
  displayName: string
  directUrl: string | null
  allowedHosts: string[]
  fileFormat: "csv" | "json" | "zip"
  parserKind: "occupation" | "major" | "employment"
  enabled: boolean
  disabledReason: string | null
}

export type KnowledgeSyncSummary = {
  runId: number
  mode: "official" | "dynamic"
  status: "completed" | "partial" | "failed" | "running"
  addedRoles: number
  addedMajors: number
  skippedRows: number
  errors: string[]
}
