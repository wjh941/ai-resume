// @vitest-environment jsdom
// 真实挂载测试：验证长文本折叠/展开的可访问性行为与状态重置。
import { describe, expect, it } from "vitest"
import { mount } from "@vue/test-utils"

import ExpandableText from "../components/ExpandableText.vue"

const longText = "长".repeat(160)

describe("ExpandableText 真实挂载", () => {
  it("短文本直接完整展示，不渲染展开按钮", () => {
    const wrapper = mount(ExpandableText, { props: { text: "一段很短的内容" } })

    expect(wrapper.find(".expandable-toggle").exists()).toBe(false)
    expect(wrapper.find(".expandable-copy").text()).toBe("一段很短的内容")
    expect(wrapper.find(".expandable-copy").classes()).not.toContain("is-collapsed")
  })

  it("长文本默认折叠；点击展开后 aria-expanded 翻转、aria-controls 指向内容节点", async () => {
    const wrapper = mount(ExpandableText, { props: { text: longText } })
    const toggle = () => wrapper.find(".expandable-toggle")
    const copy = wrapper.find(".expandable-copy")

    expect(toggle().exists()).toBe(true)
    expect(toggle().attributes("aria-expanded")).toBe("false")
    expect(toggle().text()).toBe("展开")
    expect(copy.classes()).toContain("is-collapsed")

    await toggle().trigger("click")

    expect(toggle().attributes("aria-expanded")).toBe("true")
    expect(toggle().text()).toBe("收起")
    expect(copy.classes()).not.toContain("is-collapsed")
    expect(toggle().attributes("aria-controls")).toBe(copy.attributes("id"))

    await toggle().trigger("click")

    expect(toggle().attributes("aria-expanded")).toBe("false")
    expect(copy.classes()).toContain("is-collapsed")
  })

  it("文本变化时折叠状态重置，避免新内容沿用上一次的展开状态", async () => {
    const wrapper = mount(ExpandableText, { props: { text: longText } })

    await wrapper.find(".expandable-toggle").trigger("click")
    expect(wrapper.find(".expandable-copy").classes()).not.toContain("is-collapsed")

    await wrapper.setProps({ text: `${longText}（更新于 2026-09）` })

    expect(wrapper.find(".expandable-copy").classes()).toContain("is-collapsed")
    expect(wrapper.find(".expandable-toggle").attributes("aria-expanded")).toBe("false")
  })
})
