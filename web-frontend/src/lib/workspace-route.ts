import type { WorkspaceView } from "../components/WebSidebar.vue"

export type WorkspaceRoute = {
  view: WorkspaceView
  draftId: string | null
}

type WorkspaceLocation = Pick<Location, "search">

const workspaceViews: readonly WorkspaceView[] = [
  "overview",
  "resume",
  "career",
  "jobs",
  "applications",
  "evidence",
  "membership",
  "assessment",
  "comparison",
  "insights",
  "account",
]

const pageTitles: Record<WorkspaceView, string> = {
  overview: "工作概览",
  resume: "简历中心",
  career: "职业规划",
  jobs: "职位机会",
  applications: "投递管理",
  evidence: "经历证据",
  membership: "会员与订阅",
  assessment: "职业测评",
  comparison: "岗位对比",
  insights: "年度洞察",
  account: "账户设置",
}

function isWorkspaceView(value: string | null): value is WorkspaceView {
  return value !== null && workspaceViews.includes(value as WorkspaceView)
}

export function parseWorkspaceRoute(location: WorkspaceLocation): WorkspaceRoute {
  const params = new URLSearchParams(location.search)
  const draftId = params.get("draft")?.trim() || null
  const requestedView = params.get("view")

  return {
    view: draftId ? "resume" : isWorkspaceView(requestedView) ? requestedView : "overview",
    draftId,
  }
}

export function buildWorkspaceUrl(route: WorkspaceRoute, currentUrl: string): string {
  const url = new URL(currentUrl, "http://workspace.local")
  url.searchParams.set("view", route.view)
  if (route.draftId) url.searchParams.set("draft", route.draftId)
  else url.searchParams.delete("draft")
  const search = url.searchParams.toString()
  return `${url.pathname}${search ? `?${search}` : ""}${url.hash}`
}

export function getWorkspacePageTitle(route: WorkspaceRoute): string {
  return route.draftId ? `编辑简历 · ${pageTitles.resume}` : `${pageTitles[route.view]} · 求职成长工作台`
}
