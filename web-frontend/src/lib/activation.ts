import type { OverviewState } from "./dashboard"

export type ActivationStep = {
  label: string
  target: "resume" | "career" | "applications"
  state: "done" | "current" | "next"
}

export function getActivationSteps(state: OverviewState): ActivationStep[] {
  const steps = [
    { label: "创建第一份简历", target: "resume" as const, complete: state.draftCount > 0 },
    { label: "制定一项职业行动", target: "career" as const, complete: state.openTaskCount > 0 },
    { label: "记录第一条投递", target: "applications" as const, complete: state.applicationCount > 0 },
  ]
  let currentAssigned = false
  return steps.map(({ label, target, complete }) => {
    if (complete) return { label, target, state: "done" as const }
    if (!currentAssigned) {
      currentAssigned = true
      return { label, target, state: "current" as const }
    }
    return { label, target, state: "next" as const }
  })
}
