// @vitest-environment jsdom

import { flushPromises, mount } from "@vue/test-utils"
import { beforeEach, describe, expect, it, vi } from "vitest"

import ResumeView from "../views/ResumeView.vue"
import { deleteDraft, listDraftsPage, saveDraft } from "../lib/drafts"

vi.mock("../lib/drafts", () => ({
  DRAFT_PAGE_SIZE: 20,
  copyDraft: vi.fn(),
  deleteDraft: vi.fn(),
  listDrafts: vi.fn(),
  listDraftsPage: vi.fn(),
  saveDraft: vi.fn(),
}))

const listDraftsPageMock = vi.mocked(listDraftsPage)
const deleteDraftMock = vi.mocked(deleteDraft)
const saveDraftMock = vi.mocked(saveDraft)

const AsyncButtonStub = {
  inheritAttrs: false,
  props: { loading: Boolean, disabled: Boolean, type: { type: String, default: "button" } },
  emits: ["click"],
  template: "<button v-bind='$attrs' :type='type' :disabled='disabled || loading' @click='$emit(\"click\", $event)'><slot /></button>",
}

const ErrorNoticeStub = {
  props: { message: { type: String, required: true } },
  template: "<div role='alert'>{{ message }}<slot /></div>",
}

const global = {
  stubs: {
    AsyncButton: AsyncButtonStub,
    ErrorNotice: ErrorNoticeStub,
    ExpandableText: { template: "<span><slot /></span>", props: { text: String } },
    LoadingSpinner: true,
    ProgressiveListSentinel: true,
  },
}

beforeEach(() => {
  vi.clearAllMocks()
  listDraftsPageMock.mockResolvedValue({ items: [], total: 0, limit: 20, offset: 0 })
})

describe("ResumeView creation flow", () => {
  it("shows a new resume action instead of directing users to the mini-program", async () => {
    const wrapper = mount(ResumeView, { global })
    await flushPromises()

    expect(wrapper.text()).toContain("新建简历")
    expect(wrapper.text()).not.toContain("请先在小程序")
  })

  it("creates a draft and emits its id", async () => {
    saveDraftMock.mockResolvedValue({ id: "draft-1" } as never)
    const wrapper = mount(ResumeView, { global })
    await flushPromises()

    await wrapper.get("button[data-action='new-resume']").trigger("click")
    await wrapper.get("input[name='new-job-title']").setValue("数据分析师")
    await wrapper.get("form.resume-create-form").trigger("submit")
    await flushPromises()

    expect(saveDraftMock).toHaveBeenCalledWith(expect.objectContaining({
      jobTitle: "数据分析师",
      templateId: "business",
    }))
    expect(wrapper.emitted("open-draft")?.[0]).toEqual(["draft-1"])
  })
})

describe("ResumeView draft pagination", () => {
  it("requests server pages by limit/offset and drives the pager from total", async () => {
    const firstPage = { items: Array.from({ length: 20 }, (_, index) => ({ id: `draft-${index}` })), total: 35, limit: 20, offset: 0 }
    const secondPage = { items: Array.from({ length: 15 }, (_, index) => ({ id: `late-${index}` })), total: 35, limit: 20, offset: 20 }
    listDraftsPageMock
      .mockResolvedValueOnce(firstPage as never)
      .mockResolvedValueOnce(secondPage as never)

    const wrapper = mount(ResumeView, { global })
    await flushPromises()

    expect(listDraftsPageMock).toHaveBeenNthCalledWith(1, 20, 0)
    expect(wrapper.text()).toContain("第 1 / 2 页 · 共 35 份")

    await wrapper.get("button[aria-label='下一页']").trigger("click")
    await flushPromises()

    expect(listDraftsPageMock).toHaveBeenNthCalledWith(2, 20, 20)
    expect(wrapper.text()).toContain("第 2 / 2 页 · 共 35 份")
    expect(wrapper.get("button[aria-label='下一页']").attributes("disabled")).toBeDefined()
  })

  it("backs up to the previous page after deleting the last draft of the current page", async () => {
    const confirmSpy = vi.spyOn(window, "confirm").mockReturnValue(true)
    try {
      const fullPage = (total: number, offset: number) => ({
        items: Array.from({ length: 20 }, (_, index) => ({ id: `draft-${offset + index}` })),
        total,
        limit: 20,
        offset,
      })
      listDraftsPageMock
        .mockResolvedValueOnce(fullPage(21, 0) as never)
        .mockResolvedValueOnce({ items: [{ id: "draft-20" }], total: 21, limit: 20, offset: 20 } as never)
        .mockResolvedValueOnce(fullPage(20, 0) as never)
      deleteDraftMock.mockResolvedValue(undefined)

      const wrapper = mount(ResumeView, { global })
      await flushPromises()
      await wrapper.get("button[aria-label='下一页']").trigger("click")
      await flushPromises()
      expect(wrapper.text()).toContain("第 2 / 2 页 · 共 21 份")

      await wrapper.get("article .danger-action").trigger("click")
      await flushPromises()

      expect(deleteDraftMock).toHaveBeenCalledWith("draft-20")
      expect(listDraftsPageMock).toHaveBeenNthCalledWith(3, 20, 0)
      // 回退后 total=20 只剩一页,分页控件(含计数文案)随之隐藏,列表仍完整渲染 20 条。
      expect(wrapper.findAll("article")).toHaveLength(20)
      expect(wrapper.text()).not.toContain("上一页")
    } finally {
      confirmSpy.mockRestore()
    }
  })
})
