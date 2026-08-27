import { readItems, requestApi } from "./api"

type Requester = <T>(path: string, init?: RequestInit) => Promise<T>
export type RawTask = { id: string; title?: string; description?: string; due_date?: string; status?: string }
export type RawApplication = { id: string; company?: string; role_name?: string; status?: string; next_action_at?: string; updated_at?: string }
export type RawDraft = { id: string; job_title?: string; updated_at?: string; resume?: { basic?: { name?: string; phone?: string; email?: string; city?: string }; job?: { target_role?: string } } }
export type DashboardInput = { applications: RawApplication[] | { items?: RawApplication[] }; drafts: RawDraft[] | { items?: RawDraft[] }; tasks: RawTask[] | { items?: RawTask[] } }
export type FocusAction = { kind: "task" | "application" | "resume" | "career" | "applications"; id?: string; title: string; description?: string; target: "resume" | "career" | "applications" }
export type ProgressItem = { kind: "resume" | "career" | "applications"; label: string; state: "not-started" | "in-progress" | "completed" }
export type ContinuationItem = FocusAction
export type OverviewState = { applicationCount: number; draftCount: number; openTaskCount: number; focus: FocusAction; focusOptions: FocusAction[]; progress: ProgressItem[]; continuations: ContinuationItem[]; hasWorkspaceData: boolean }

const terminalApplications = new Set(["offer", "rejected", "closed"])
const genericTitles = { task: "Continue the next career action", application: "Continue an application action", resume: "Take Action: start your first resume", career: "Plan your next career action", applications: "Review your applications" }
function validDate(value?: string) { if (!value) return undefined; const time = Date.parse(value); return Number.isNaN(time) ? undefined : time }
function compareByDate<T extends { id: string }>(field: keyof T) { return (left: T, right: T) => { const a = validDate(left[field] as string | undefined); const b = validDate(right[field] as string | undefined); if (a === undefined && b !== undefined) return 1; if (a !== undefined && b === undefined) return -1; if (a !== undefined && b !== undefined && a !== b) return a - b; return left.id.localeCompare(right.id) } }
function nonEmpty(value: unknown): value is string { return typeof value === "string" && value.trim().length > 0 }
function normalize(input: DashboardInput) { return { applications: readItems(input.applications), drafts: readItems(input.drafts), tasks: readItems(input.tasks) } }

function candidatesFor(input: DashboardInput): FocusAction[] {
  const { applications, drafts, tasks } = normalize(input)
  const incompleteTasks = tasks.filter((task) => task.status !== "completed").sort(compareByDate<RawTask>("due_date"))
  const activeApplications = applications.filter((application) => !terminalApplications.has(application.status || "")).filter((application) => application.next_action_at).sort(compareByDate<RawApplication>("next_action_at"))
  const candidates: FocusAction[] = []
  const add = (action: FocusAction) => { if (!candidates.some((candidate) => candidate.kind === action.kind && candidate.id === action.id)) candidates.push(action) }
  const task = incompleteTasks[0]; if (task) add({ kind: "task", id: task.id, title: task.title || genericTitles.task, description: task.description, target: "career" })
  const application = activeApplications[0]; if (application) add({ kind: "application", id: application.id, title: application.company && application.role_name ? `Follow up: ${application.company} - ${application.role_name}` : genericTitles.application, target: "applications" })
  if (!drafts.length) add({ kind: "resume", title: genericTitles.resume, target: "resume" }); else if (!tasks.length) add({ kind: "career", title: genericTitles.career, target: "career" })
  if (!task && !application) add({ kind: "applications", title: genericTitles.applications, target: "applications" })
  for (const starter of [
    { kind: "resume" as const, title: genericTitles.resume, target: "resume" as const },
    { kind: "career" as const, title: genericTitles.career, target: "career" as const },
    { kind: "applications" as const, title: genericTitles.applications, target: "applications" as const },
  ]) {
    if (candidates.length >= 3) break
    add(starter)
  }
  return candidates.slice(0, 3)
}

export function selectFocusAction(input: DashboardInput, offset = 0): FocusAction { const options = candidatesFor(input); return options[((offset % options.length) + options.length) % options.length] }
export function buildOverviewState(input: DashboardInput): OverviewState {
  const { applications, drafts, tasks } = normalize(input); const focusOptions = candidatesFor(input); const focus = focusOptions[0]
  const resumeComplete = drafts.length > 0 && drafts.every((draft) => { const basic = draft.resume?.basic; return [basic?.name, basic?.phone, basic?.email, basic?.city, draft.resume?.job?.target_role].every(nonEmpty) })
  const progress: ProgressItem[] = [
    { kind: "resume", label: "Resume", state: !drafts.length ? "not-started" : resumeComplete ? "completed" : "in-progress" },
    { kind: "career", label: "Career plan", state: !tasks.length ? "not-started" : tasks.every((task) => task.status === "completed") ? "completed" : "in-progress" },
    { kind: "applications", label: "Applications", state: !applications.length ? "not-started" : applications.every((application) => terminalApplications.has(application.status || "")) ? "completed" : "in-progress" },
  ]
  const continuations = [...tasks.filter((task) => task.status !== "completed").sort(compareByDate<RawTask>("due_date")).map((task): ContinuationItem => ({ kind: "task", id: task.id, title: task.title || genericTitles.task, description: task.description, target: "career" })), ...applications.filter((application) => !terminalApplications.has(application.status || "")).map((application): ContinuationItem => ({ kind: "application", id: application.id, title: application.company && application.role_name ? `Follow up: ${application.company} - ${application.role_name}` : genericTitles.application, target: "applications" })), ...drafts.map((draft): ContinuationItem => ({ kind: "resume", id: draft.id, title: draft.job_title ? `Continue: ${draft.job_title}` : "Continue your resume", target: "resume" }))].filter((item) => !(item.kind === focus.kind && item.id === focus.id)).slice(0, 3)
  return { applicationCount: applications.length, draftCount: drafts.length, openTaskCount: tasks.filter((task) => task.status !== "completed").length, focus, focusOptions, progress, continuations, hasWorkspaceData: Boolean(applications.length || drafts.length || tasks.length) }
}

type ItemsResponse = RawApplication[] | RawTask[] | { items?: RawApplication[] | RawTask[] }
type DraftListResponse = RawDraft[] | { items?: RawDraft[] }
export async function loadOverview(request: Requester = requestApi, planId = "web-workspace"): Promise<OverviewState> {
  const [applications, drafts, tasks] = await Promise.all([request<ItemsResponse>("/api/applications"), request<DraftListResponse>("/api/draft/list"), request<ItemsResponse>(`/api/career/tasks?plan_id=${encodeURIComponent(planId)}`)])
  return buildOverviewState({ applications: applications as DashboardInput["applications"], drafts, tasks: tasks as DashboardInput["tasks"] })
}
