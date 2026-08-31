// @vitest-environment jsdom

import { flushPromises, mount } from "@vue/test-utils"
import { defineComponent, readonly, ref, type Ref } from "vue"
import { beforeEach, describe, expect, it, vi } from "vitest"

import LoginPanel from "../components/LoginPanel.vue"
import MembershipPackageCard from "../components/MembershipPackageCard.vue"
import InsightsView from "../views/InsightsView.vue"
import JobsView from "../views/JobsView.vue"
import { requestApi } from "../lib/api"
import { loginWithPassword, loginWithPhone, registerAccount } from "../lib/auth"
import {
  CAPABILITIES_KEY,
  createCapabilityContext,
  defaultCapabilities,
  type Capabilities,
  type CapabilityContext,
} from "../lib/capabilities"
import type { MembershipPackage } from "../lib/membership"

vi.mock("../lib/auth", () => ({
  loginWithPassword: vi.fn(),
  loginWithPhone: vi.fn(),
  registerAccount: vi.fn(),
}))

vi.mock("../lib/api", () => ({
  requestApi: vi.fn(),
}))

const requestApiMock = vi.mocked(requestApi)
const loginWithPasswordMock = vi.mocked(loginWithPassword)
const loginWithPhoneMock = vi.mocked(loginWithPhone)
const registerAccountMock = vi.mocked(registerAccount)

const ErrorNoticeStub = defineComponent({
  props: { message: { type: String, required: true } },
  template: '<div role="alert"><span class="error-message">{{ message }}</span><slot /></div>',
})

const AsyncButtonStub = defineComponent({
  inheritAttrs: false,
  props: {
    loading: Boolean,
    disabled: Boolean,
    type: { type: String, default: "button" },
  },
  emits: ["click"],
  template: '<button v-bind="$attrs" :type="type" :disabled="disabled || loading" :aria-busy="loading || undefined" @click="$emit(\'click\', $event)"><slot /></button>',
})

const ExpandableTextStub = defineComponent({
  props: { text: { type: String, required: true } },
  template: "<span>{{ text }}</span>",
})

function testCapabilities(overrides: Partial<Capabilities> = {}): {
  context: CapabilityContext
  state: Ref<Capabilities>
  refreshing: Ref<boolean>
  refresh: ReturnType<typeof vi.fn>
} {
  const state = ref<Capabilities>({ ...defaultCapabilities(), ...overrides })
  const refreshing = ref(false)
  const refresh = vi.fn(async () => state.value)
  return {
    context: { capabilities: readonly(state), refreshing: readonly(refreshing), refresh },
    state,
    refreshing,
    refresh,
  }
}

function enabled(notice = "enabled") {
  return { enabled: true, mode: "real" as const, notice }
}

function disabled(notice = "temporarily disabled") {
  return { enabled: false, mode: "disabled" as const, notice }
}

const viewStubs = {
  AsyncButton: AsyncButtonStub,
  ErrorNotice: ErrorNoticeStub,
  ExpandableText: ExpandableTextStub,
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe("LoginPanel capability gates", () => {
  it("disables SMS, blocks send-code after a live capability change, and keeps password login available", async () => {
    const test = testCapabilities({ smsLogin: enabled("SMS available") })
    const wrapper = mount(LoginPanel, {
      global: {
        provide: { [CAPABILITIES_KEY]: test.context },
        stubs: { AsyncButton: AsyncButtonStub, ErrorNotice: ErrorNoticeStub },
      },
    })

    const tabs = wrapper.findAll('[role="tab"]')
    expect(tabs[1].attributes("disabled")).toBeUndefined()
    await tabs[1].trigger("click")
    await wrapper.find('input[autocomplete="tel"]').setValue("13800138000")

    test.state.value = { ...test.state.value, smsLogin: disabled("SMS login is unavailable") }
    await wrapper.vm.$nextTick()

    expect(tabs[1].element).toHaveProperty("disabled", true)
    expect(wrapper.text()).toContain("SMS login is unavailable")
    await wrapper.find(".verification-row button").trigger("click")
    expect(requestApiMock).not.toHaveBeenCalledWith("/api/auth/send-code", expect.anything())

    await tabs[0].trigger("click")
    await wrapper.find('input[autocomplete="username"]').setValue("candidate")
    await wrapper.find('input[type="password"]').setValue("long-enough-password")
    loginWithPasswordMock.mockResolvedValueOnce({ token: "token", user: { id: "1", account: "candidate" } } as never)
    await wrapper.find("form").trigger("submit")
    await flushPromises()

    expect(loginWithPasswordMock).toHaveBeenCalledWith(requestApi, "candidate", "long-enough-password")
    expect(loginWithPhoneMock).not.toHaveBeenCalled()
    expect(registerAccountMock).not.toHaveBeenCalled()
  })
})

describe("MembershipPackageCard capability gates", () => {
  const packageFixture: MembershipPackage = {
    packageType: "monthly",
    name: "Monthly",
    vipLevel: "pro",
    durationDays: 30,
    totalAmount: 19,
    benefits: ["Benefit"],
  }

  it("disables payment and emits no purchase while payment is unavailable", async () => {
    const wrapper = mount(MembershipPackageCard, {
      props: {
        package: packageFixture,
        currentVip: null,
        pending: false,
        paymentEnabled: false,
        paymentNotice: "Payment is unavailable",
      },
      global: { stubs: { AsyncButton: AsyncButtonStub } },
    })

    expect(wrapper.find(".source-notice").text()).toContain("Payment is unavailable")
    const button = wrapper.find("button.primary-button")
    expect(button.element).toHaveProperty("disabled", true)
    await button.trigger("click")
    expect(wrapper.emitted("purchase")).toBeUndefined()
  })

  it("emits the existing package type and auto-renew value when payment is enabled", async () => {
    const wrapper = mount(MembershipPackageCard, {
      props: {
        package: packageFixture,
        currentVip: null,
        pending: false,
        paymentEnabled: true,
        paymentNotice: "Payment is unavailable",
      },
      global: { stubs: { AsyncButton: AsyncButtonStub } },
    })

    await wrapper.find("button.primary-button").trigger("click")
    expect(wrapper.emitted("purchase")).toEqual([["monthly", false]])
  })
})

describe.each([
  {
    name: "JobsView",
    component: JobsView,
    querySelector: "/api/job/query",
    roleInput: 'input[maxlength="200"]',
    reasonId: "jobs-professional-mode-reason",
    result: { role_name: "Data analyst" },
    simplifiedPayload: { role_name: "Data analyst", report_mode: "simplified" },
    demoResult: {
      role_name: "Data analyst",
      report: { mode: "professional", summary: "Demo summary", actions: [], source_notice: "Source", evidence: [] },
    },
  },
  {
    name: "InsightsView",
    component: InsightsView,
    querySelector: "/api/career/annual-insights/query",
    roleInput: 'input[maxlength="120"]',
    reasonId: "insights-professional-mode-reason",
    result: {
      report: {
        mode: "simplified",
        summary: "Summary",
        actions: [],
        source_notice: "Source",
        evidence: [],
      },
    },
    demoResult: {
      report: {
        mode: "professional",
        summary: "Demo summary",
        actions: [],
        source_notice: "Source",
        evidence: [],
      },
    },
    simplifiedPayload: { role_name: "Data analyst", year: 2024, report_mode: "simplified" },
  },
])("$name capability gates", ({ component, querySelector, roleInput, reasonId, result, demoResult, simplifiedPayload }) => {
  function mountView() {
    const test = testCapabilities({ jobMatching: disabled("Professional matching is unavailable") })
    const wrapper = mount(component, {
      global: { provide: { [CAPABILITIES_KEY]: test.context }, stubs: viewStubs },
    })
    return { wrapper, ...test }
  }

  it("disables professional mode with a linked reason and keeps recovery actions in the mode area", async () => {
    const { wrapper } = mountView()
    await wrapper.find(roleInput).setValue("Data analyst")
    const professional = wrapper.find("button.is-unavailable")
    expect(professional.element).toHaveProperty("disabled", true)
    expect(professional.attributes("aria-describedby")).toBe(reasonId)
    expect(wrapper.find(`#${reasonId}`).text()).toContain("Professional matching is unavailable")
    expect(wrapper.find(".mode-switch").text()).toContain("重试服务状态")
    expect(wrapper.find(".mode-switch").text()).toContain("查看会员权益")

    await professional.trigger("click")
    expect(wrapper.find("button.is-selected").text()).toContain("精简版")
    ;(wrapper.vm as unknown as { reportMode: "simplified" | "professional" }).reportMode = "professional"
    await wrapper.find("form").trigger("submit")
    await flushPromises()
    expect(requestApiMock).not.toHaveBeenCalledWith(querySelector, expect.anything())
    await wrapper.find(".mode-switch button.notice-action:last-child").trigger("click")
    expect(wrapper.emitted("navigate")).toEqual([["membership"]])
  })

  it("retries the shared capability state without automatically submitting a query", async () => {
    const { wrapper, refresh, state } = mountView()
    refresh.mockImplementationOnce(async () => {
      state.value = { ...state.value, jobMatching: enabled("Matching enabled") }
      return state.value
    })
    await wrapper.find(roleInput).setValue("Data analyst")
    const retry = wrapper.findAll(".mode-switch button.notice-action").find((button) => button.text().includes("重试服务状态"))
    expect(retry).toBeDefined()
    await retry!.trigger("click")
    await flushPromises()

    expect(refresh).toHaveBeenCalledTimes(1)
    expect(requestApiMock).not.toHaveBeenCalledWith(querySelector, expect.anything())
    expect(wrapper.find("button.is-unavailable").exists()).toBe(false)
  })

  it("describes the shared loading state and disables professional mode", async () => {
    const test = testCapabilities({ jobMatching: enabled("Matching enabled") })
    test.refreshing.value = true
    const wrapper = mount(component, {
      global: { provide: { [CAPABILITIES_KEY]: test.context }, stubs: viewStubs },
    })

    const professional = wrapper.findAll("button").find((button) => button.text().includes("专业版"))!
    expect(professional.element).toHaveProperty("disabled", true)
    expect(professional.attributes("aria-describedby")).toBe(reasonId)
    expect(wrapper.find(`#${reasonId}`).text()).toContain("检查中")
  })

  it("labels demo professional results and discloses non-real-time source data", async () => {
    const test = testCapabilities({ jobMatching: { enabled: true, mode: "demo", notice: "Local demo matching" } })
    const wrapper = mount(component, {
      global: { provide: { [CAPABILITIES_KEY]: test.context }, stubs: viewStubs },
    })
    requestApiMock.mockResolvedValueOnce(demoResult)
    await wrapper.find(roleInput).setValue("Data analyst")
    const professional = wrapper.findAll("button").find((button) => button.text().includes("专业版"))!
    await professional.trigger("click")
    await wrapper.find("form").trigger("submit")
    await flushPromises()

    expect(wrapper.find("button.is-selected").text()).toContain("专业版（演示）")
    expect(wrapper.find(".report-mode-label").text()).toContain("专业版（演示）")
    expect(wrapper.text()).toContain("本地/演示数据不代表实时职位或真实市场洞察")
  })

  it("keeps simplified queries on the unchanged endpoint and payload", async () => {
    const { wrapper } = mountView()
    await wrapper.find(roleInput).setValue("Data analyst")
    if (component === InsightsView) await wrapper.find('input[type="number"]').setValue("2024")
    requestApiMock.mockResolvedValueOnce(result)
    await wrapper.find("form").trigger("submit")
    await flushPromises()

    expect(requestApiMock).toHaveBeenCalledWith(querySelector, {
      method: "POST",
      body: JSON.stringify(simplifiedPayload),
    })
  })
})

describe("shared capability context runtime", () => {
  it("shares refreshed state across mounted consumers and reflects refresh loading on both retry controls", async () => {
    let resolveHealth!: (value: unknown) => void
    requestApiMock.mockReturnValueOnce(new Promise((resolve) => { resolveHealth = resolve }))
    const context = createCapabilityContext()
    const Parent = defineComponent({
      components: { JobsView, InsightsView },
      template: '<div><JobsView /><InsightsView /></div>',
    })
    const wrapper = mount(Parent, {
      global: { provide: { [CAPABILITIES_KEY]: context }, stubs: viewStubs },
    })

    const forms = wrapper.findAll("form")
    await forms[0].find('input[maxlength="200"]').setValue("Data analyst")
    await forms[1].find('input[maxlength="120"]').setValue("Data analyst")
    await wrapper.vm.$nextTick()

    const retries = wrapper.findAll("button.notice-action")
    expect(retries).toHaveLength(4)

    const first = context.refresh()
    const second = context.refresh()
    expect(requestApiMock).toHaveBeenCalledTimes(1)
    expect(context.refreshing.value).toBe(true)
    await wrapper.vm.$nextTick()

    expect(retries.filter((button) => button.element.disabled)).toHaveLength(2)
    expect(retries.filter((button) => button.attributes("aria-busy") === "true")).toHaveLength(2)

    resolveHealth({ features: { job_matching: { enabled: true, mode: "real", notice: "Matching enabled" } } })
    await Promise.all([first, second])
    await wrapper.vm.$nextTick()

    expect(wrapper.findAll(".mode-notice")).toHaveLength(0)
    expect(wrapper.findAll("button.is-unavailable")).toHaveLength(0)
    expect(context.refreshing.value).toBe(false)
  })
})
