// @vitest-environment jsdom

import { flushPromises, mount } from "@vue/test-utils"
import { beforeEach, describe, expect, it, vi } from "vitest"

import ResumeView from "../views/ResumeView.vue"
import { listDrafts, saveDraft } from "../lib/drafts"

vi.mock("../lib/drafts", () => ({
  copyDraft: vi.fn(),
  deleteDraft: vi.fn(),
  listDrafts: vi.fn(),
  saveDraft: vi.fn(),
}))

const listDraftsMock = vi.mocked(listDrafts)
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
  listDraftsMock.mockResolvedValue([])
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
