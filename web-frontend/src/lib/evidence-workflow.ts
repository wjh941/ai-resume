import type { EvidenceRecord } from "./evidence"

export function replaceEvidence(items: EvidenceRecord[], updated: EvidenceRecord): EvidenceRecord[] {
  return items.map((item) => item.id === updated.id ? updated : item)
}

export function removeEvidence(items: EvidenceRecord[], id: string): EvidenceRecord[] {
  return items.filter((item) => item.id !== id)
}

export function toggleVerified(item: EvidenceRecord, verified: boolean): EvidenceRecord {
  return { ...item, verified }
}
