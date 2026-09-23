// @vitest-environment jsdom
// 真实挂载测试：登录面板是 Web 工作台的核心入口，验证双模式渲染、
// 能力门控（smsLogin 关闭时禁用手机号登录）与提交链路（成功 emit / 失败提示）。
import { beforeEach, describe, expect, it, vi } from "vitest"
import { mount } from "@vue/test-utils"
import { ref } from "vue"
import type { App } from "vue"

import LoginPanel from "../components/LoginPanel.vue"
import ErrorNotice from "../components/ErrorNotice.vue"
import { CAPABILITIES_KEY } from "../lib/capabilities"
import type { CapabilityContext, Capabilities } from "../lib/capabilities"
import type { Session } from "../lib/session"
import { loginWithPassword, registerAccount } from "../lib/auth"
import { requestApi } from "../lib/api"

vi.mock("../lib/auth", () => ({
  loginWithPassword: vi.fn(),
  loginWithPhone: vi.fn(),
  registerAccount: vi.fn(),
}))

vi.mock("../lib/api", () => ({
  requestApi: vi.fn(),
  SLOW_REQUEST_TIMEOUT_MS: 120_000,
}))

const fakeSession: Session = { token: "jwt-token", user: { user_id: "u-1", role: "user" } }

const capabilities = (smsLogin: Capabilities["smsLogin"]): Capabilities => ({
  resumeImport: { enabled: false, mode: "disabled", notice: "简历导入暂不可用" },
  smsLogin,
  wechatOauth: { enabled: false, mode: "disabled", notice: "微信登录暂不可用" },
  payment: { enabled: false, mode: "disabled", notice: "支付暂不可用" },
  pushNotifications: { enabled: false, mode: "disabled", notice: "推送暂不可用" },
  jobMatching: { enabled: true, mode: "real", notice: "可用" },
})

// 与 main.ts 保持一致：ErrorNotice 是全局注册组件；
// 能力上下文用 app.provide 注入，保证组件 inject(CAPABILITIES_KEY) 命中。
const mountPanel = (smsLogin: Capabilities["smsLogin"]) => {
  const caps = capabilities(smsLogin)
  const context: CapabilityContext = {
    capabilities: ref(caps),
    refreshing: ref(false),
    refresh: vi.fn(async () => caps),
  }
  const capabilityPlugin = { install: (app: App) => app.provide(CAPABILITIES_KEY, context) }
  return mount(LoginPanel, {
    global: {
      components: { ErrorNotice },
      plugins: [capabilityPlugin],
    },
  })
}

const demoSms = (notice = "演示验证码 123456") => ({ enabled: true, mode: "demo" as const, notice })
const disabledSms = () => ({
  enabled: false,
  mode: "disabled" as const,
  notice: "短信验证码登录暂不可用，请使用账号密码登录",
})

beforeEach(() => {
  vi.clearAllMocks()
})

describe("LoginPanel 真实挂载", () => {
  it("默认渲染账号密码登录表单，账号与密码输入框带正确的自动填充标注", () => {
    const wrapper = mountPanel(demoSms())

    expect(wrapper.find("input[autocomplete='username']").exists()).toBe(true)
    expect(wrapper.find("input[autocomplete='current-password']").exists()).toBe(true)
    expect(wrapper.find("form").exists()).toBe(true)
    // 能力可用时不展示能力提示
    expect(wrapper.find(".capability-notice").exists()).toBe(false)
  })

  it("smsLogin 能力关闭时：手机号入口禁用且页面解释原因，而不是静默失败", () => {
    const wrapper = mountPanel(disabledSms())

    const tabs = wrapper.findAll("[role='tab']")
    expect(tabs).toHaveLength(2)
    expect(tabs[0].attributes("disabled")).toBeUndefined()
    expect(tabs[1].attributes("disabled")).toBeDefined()
    expect(wrapper.find(".capability-notice").text()).toContain("短信验证码登录暂不可用")
  })

  it("手机号模式下，非法手机号点击获取验证码只给本地校验错误，不发起请求", async () => {
    const wrapper = mountPanel(demoSms())

    await wrapper.findAll("[role='tab']")[1].trigger("click")
    const phone = wrapper.find("input[autocomplete='tel']")
    expect(phone.exists()).toBe(true)

    await phone.setValue("123")
    const sendButton = wrapper.findAll("button").find((b) => b.text().includes("获取验证码"))
    await sendButton!.trigger("click")

    expect(wrapper.text()).toContain("请填写正确的 11 位手机号")
    expect(requestApi).not.toHaveBeenCalled()
  })

  it("账号密码提交成功：调用登录库并向上抛出 authenticated 会话", async () => {
    vi.mocked(loginWithPassword).mockResolvedValue(fakeSession)
    const wrapper = mountPanel(demoSms())

    await wrapper.find("input[autocomplete='username']").setValue("demo_user")
    await wrapper.find("input[autocomplete='current-password']").setValue("super-secret-pw")
    await wrapper.find("form").trigger("submit")
    await vi.waitFor(() => {
      expect(wrapper.emitted("authenticated")).toBeTruthy()
    })

    expect(loginWithPassword).toHaveBeenCalledWith(expect.anything(), "demo_user", "super-secret-pw")
    expect(wrapper.emitted("authenticated")![0]).toEqual([fakeSession])
    // 成功后 loading 复位，按钮恢复可点
    expect(wrapper.find("button[type='submit']").attributes("aria-busy")).toBeUndefined()
  })

  it("登录失败：错误经 ErrorNotice 以 role=alert 呈现，且不 emit 会话", async () => {
    vi.mocked(loginWithPassword).mockRejectedValue(new Error("账号或密码不正确"))
    const wrapper = mountPanel(demoSms())

    await wrapper.find("input[autocomplete='username']").setValue("demo_user")
    await wrapper.find("input[autocomplete='current-password']").setValue("wrong-password")
    await wrapper.find("form").trigger("submit")
    await vi.waitFor(() => {
      expect(wrapper.find("#login-error").exists()).toBe(true)
    })

    expect(wrapper.find("#login-error").attributes("role")).toBe("alert")
    expect(wrapper.text()).toContain("账号或密码不正确")
    expect(wrapper.emitted("authenticated")).toBeUndefined()
  })

  it("注册模式切换：入口链接在登录/注册之间往复，提交走 registerAccount", async () => {
    vi.mocked(registerAccount).mockResolvedValue(fakeSession)
    const wrapper = mountPanel(demoSms())

    await wrapper.find("button.form-link").trigger("click")
    await wrapper.find("input[autocomplete='username']").setValue("new_user")
    await wrapper.find("input[autocomplete='current-password']").setValue("a-long-password")
    await wrapper.find("form").trigger("submit")
    await vi.waitFor(() => {
      expect(wrapper.emitted("authenticated")).toBeTruthy()
    })

    expect(registerAccount).toHaveBeenCalled()
    expect(loginWithPassword).not.toHaveBeenCalled()
  })
})
