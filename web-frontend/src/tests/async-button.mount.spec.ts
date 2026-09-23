// @vitest-environment jsdom
// 真实挂载测试：与 src/tests 下既有「源码契约」断言互补，这里验证组件真实渲染行为。
import { describe, expect, it } from "vitest"
import { mount } from "@vue/test-utils"

import AsyncButton from "../components/AsyncButton.vue"
import LoadingSpinner from "../components/LoadingSpinner.vue"

describe("AsyncButton 真实挂载", () => {
  it("空闲时渲染标签且可点击，loading 时禁用并标记 aria-busy", async () => {
    const wrapper = mount(AsyncButton, { slots: { default: "保存草稿" } })
    const button = wrapper.find("button")

    expect(button.attributes("type")).toBe("button")
    expect(button.text()).toContain("保存草稿")
    expect(button.attributes("disabled")).toBeUndefined()
    expect(button.attributes("aria-busy")).toBeUndefined()
    expect(wrapper.findComponent(LoadingSpinner).exists()).toBe(false)

    await wrapper.setProps({ loading: true })

    expect(button.attributes("disabled")).toBeDefined()
    expect(button.attributes("aria-busy")).toBe("true")
    expect(button.classes()).toContain("is-loading")
    const spinner = wrapper.findComponent(LoadingSpinner)
    expect(spinner.exists()).toBe(true)
    expect(spinner.classes()).toContain("loading-spinner-sm")
  })

  it("loading 与 disabled 任一为真都会禁用按钮，防止重复提交", async () => {
    const wrapper = mount(AsyncButton, {
      props: { disabled: true, type: "submit" },
      slots: { default: "提交" },
    })
    const button = wrapper.find("button")

    expect(button.attributes("type")).toBe("submit")
    expect(button.attributes("disabled")).toBeDefined()

    await wrapper.setProps({ disabled: false })
    expect(button.attributes("disabled")).toBeUndefined()

    await wrapper.setProps({ loading: true })
    expect(button.attributes("disabled")).toBeDefined()
  })
})
