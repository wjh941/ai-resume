type UniLike = {
  switchTab?: (options: { url: string; fail?: () => void }) => void
  redirectTo?: (options: { url: string; fail?: () => void }) => void
  showToast?: (options: { title: string; icon?: string }) => void
}

function uniLike(): UniLike {
  return (globalThis as typeof globalThis & { uni?: UniLike }).uni ?? {}
}

function notifyNavigationFailure(): void {
  uniLike().showToast?.({ title: "页面打开失败，请稍后重试", icon: "none" })
}

/** 切换到 tabBar 核心页。switchTab 不支持查询参数；带参数的跳转请继续用 navigateTo。 */
export function goTab(url: string): void {
  uniLike().switchTab?.({ url, fail: notifyNavigationFailure })
}

/** 替换当前页前进（页面栈不增长），适合“完成后不再返回”的环形跳转，如测评→规划、编辑→投递。 */
export function redirectPage(url: string): void {
  uniLike().redirectTo?.({ url, fail: notifyNavigationFailure })
}
