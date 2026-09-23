// @vitest-environment jsdom
// 真实挂载测试：验证岗位对比胶囊选择器的选择、上限与门控行为。
import { describe, expect, it } from "vitest"
import { mount } from "@vue/test-utils"

import CapsuleMultiSelect from "../components/CapsuleMultiSelect.vue"

const OPTIONS = ["数据分析师", "前端开发工程师", "产品经理", "算法工程师"]

const mountSelect = (selected: string[], extraProps: Record<string, unknown> = {}) =>
  mount(CapsuleMultiSelect, {
    props: { options: OPTIONS, selected, ...extraProps },
  })

describe("CapsuleMultiSelect 真实挂载", () => {
  it("渲染全部岗位胶囊，点击抛出 update:selected 并切换 aria-pressed", async () => {
    const wrapper = mountSelect([])
    const chips = wrapper.findAll("button.capsule-tag")

    expect(chips).toHaveLength(OPTIONS.length)
    expect(chips[0].attributes("aria-pressed")).toBe("false")

    await chips[0].trigger("click")
    expect(wrapper.emitted("update:selected")![0]).toEqual([["数据分析师"]])

    await wrapper.setProps({ selected: ["数据分析师"] })
    expect(wrapper.findAll("button.capsule-tag")[0].attributes("aria-pressed")).toBe("true")
  })

  it("再次点击已选胶囊是取消选择", async () => {
    const wrapper = mountSelect(["产品经理"])

    await wrapper.findAll("button.capsule-tag")[2].trigger("click")

    expect(wrapper.emitted("update:selected")![0]).toEqual([[]])
  })

  it("全选按 maxSelectable 截断，重置清空选择", async () => {
    const wrapper = mountSelect([], { maxSelectable: 2 })
    const buttons = wrapper.findAll("button")

    await buttons.find((b) => b.text() === "全选")!.trigger("click")
    expect(wrapper.emitted("update:selected")![0]).toEqual([OPTIONS.slice(0, 2)])

    await buttons.find((b) => b.text() === "重置")!.trigger("click")
    expect(wrapper.emitted("update:selected")![1]).toEqual([[]])
  })

  it("选中不足 2 项时禁止开始对比，达到下限后恢复", async () => {
    const wrapper = mountSelect([])
    const submit = () => wrapper.find("button.capsule-submit")

    expect(submit().attributes("disabled")).toBeDefined()

    await wrapper.setProps({ selected: ["数据分析师", "产品经理"] })
    expect(submit().attributes("disabled")).toBeUndefined()
  })

  it("pending 期间禁用全部胶囊，防止比较中途改动选择", () => {
    const wrapper = mountSelect(["数据分析师"], { pending: true })

    for (const chip of wrapper.findAll("button.capsule-tag")) {
      expect(chip.attributes("disabled")).toBeDefined()
    }
    expect(wrapper.find("section").attributes("aria-busy")).toBe("true")
  })
})
