export type EvidenceKind =
  | "coursework"
  | "project"
  | "activity"
  | "internship"
  | "employment"

export interface ResumeEvidence {
  id: string
  clientId: string
  kind: EvidenceKind
  title: string
  context: string
  actions: string
  outcome: string
  proofNote: string
  verified: boolean
  createdAt: string
  updatedAt: string
}

export interface ResumeEvidenceInput {
  id?: string
  clientId: string
  kind: EvidenceKind
  title: string
  context: string
  actions: string
  outcome: string
  proofNote: string
  verified: boolean
}

export interface EvidenceSuggestion {
  sourceEvidenceId: string
  sourceTitle: string
  targetSection: "project" | "employment"
  title: string
  role: string
  description: string
  riskNote: string
}

export interface ResumeReadinessReport {
  ready: boolean
  blockingItems: string[]
  warningItems: string[]
}
