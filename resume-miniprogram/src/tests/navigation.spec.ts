import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import { goTab, redirectPage } from "../utils/navigation"

type SwitchTabOptions = { url: string; fail?: () => void }
type RedirectOptions = { url: string; fail?: () => void }
type ToastOptions = { title: string; icon?: string }

let switchTabMock = vi.fn()
let redirectToMock = vi.fn()
let showToastMock = vi.fn()

function installUni() {
  ;(globalThis as typeof globalThis & { uni?: unknown }).uni = {
    switchTab: (options: SwitchTabOptions) => switchTabMock(options),
    redirectTo: (options: RedirectOptions) => redirectToMock(options),
    showToast: (options: ToastOptions) => showToastMock(options),
  }
}

beforeEach(() => {
  switchTabMock = vi.fn()
  redirectToMock = vi.fn()
  showToastMock = vi.fn()
  installUni()
})

afterEach(() => {
  delete (globalThis as typeof globalThis & { uni?: unknown }).uni
})

describe("goTab", () => {
  it("switches to the tab page", () => {
    goTab("/pages/job-search/index")
    expect(switchTabMock).toHaveBeenCalledWith({ url: "/pages/job-search/index", fail: expect.any(Function) })
  })

  it("shows a toast when the switch fails", () => {
    switchTabMock.mockImplementation((options: SwitchTabOptions) => options.fail?.())
    goTab("/pages/job-search/index")
    expect(showToastMock).toHaveBeenCalledWith(expect.objectContaining({ title: "页面打开失败，请稍后重试" }))
  })

  it("does not throw when uni is unavailable", () => {
    delete (globalThis as typeof globalThis & { uni?: unknown }).uni
    expect(() => goTab("/pages/job-search/index")).not.toThrow()
  })
})

describe("redirectPage", () => {
  it("keeps query parameters so cross-page context survives", () => {
    redirectPage("/pages/applications/index?roleName=%E6%95%B0%E6%8D%AE%E5%88%86%E6%9E%90%E5%B8%88&draftId=d1")
    expect(redirectToMock).toHaveBeenCalledWith({
      url: "/pages/applications/index?roleName=%E6%95%B0%E6%8D%AE%E5%88%86%E6%9E%90%E5%B8%88&draftId=d1",
      fail: expect.any(Function),
    })
  })

  it("shows a toast when the redirect fails", () => {
    redirectToMock.mockImplementation((options: RedirectOptions) => options.fail?.())
    redirectPage("/pages/career-planner/index")
    expect(showToastMock).toHaveBeenCalledWith(expect.objectContaining({ title: "页面打开失败，请稍后重试" }))
  })
})
