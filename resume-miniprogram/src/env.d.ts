/// <reference types="vite/client" />

declare module "*.vue" {
  import type { DefineComponent } from "vue"
  const component: DefineComponent<Record<string, never>, Record<string, never>, unknown>
  export default component
}

declare module "*.js" {
  export function withReportMode(payload: Record<string, unknown>, mode: string): Record<string, unknown>
  export function normalizeReport(result: unknown): {
    mode: "simplified" | "professional"
    summary: string
    actions: unknown[]
    evidence: unknown[]
    sourceNotice: string
    upgradeNotice: string
  }
  export function visibleEvidence(report: { mode: string; evidence: unknown[] }): unknown[]
}
