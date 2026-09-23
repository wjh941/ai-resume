// @vitest-environment jsdom
// 真实挂载测试：验证 ErrorNotice 的可访问性契约与动作插槽。
import { describe, expect, it } from "vitest"
import { mount } from "@vue/test-utils"

import ErrorNotice from "../components/ErrorNotice.vue"

describe("ErrorNotice 真实挂载", () => {
  it("以 role=alert + aria-live 渲染错误消息，无动作区时不渲染 actions 容器", () => {
    const wrapper = mount(ErrorNotice, {
      props: { message: "登录未完成，请检查填写内容" },
    })

    const notice = wrapper.find("p")
    expect(notice.attributes("role")).toBe("alert")
    expect(notice.attributes("aria-live")).toBe("assertive")
    expect(wrapper.text()).toContain("登录未完成，请检查填写内容")
    expect(wrapper.find(".notice-error-actions").exists()).toBe(false)
    expect(notice.classes()).not.toContain("notice-error--compact")
  })

  it("compact 模式附加修饰类，默认插槽内容渲染为动作区", () => {
    const wrapper = mount(ErrorNotice, {
      props: { message: "验证码发送失败", compact: true },
      slots: { default: `<button type="button">改用账号密码登录</button>` },
    })

    const notice = wrapper.find("p")
    expect(notice.classes()).toContain("notice-error--compact")
    expect(notice.classes()).toContain("notice-with-action")

    const actions = wrapper.find(".notice-error-actions")
    expect(actions.exists()).toBe(true)
    expect(actions.find("button").text()).toBe("改用账号密码登录")
  })
})
