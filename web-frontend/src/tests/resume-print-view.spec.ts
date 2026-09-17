// @vitest-environment jsdom

import { existsSync, readFileSync } from "node:fs"
import { resolve } from "node:path"

import { mount } from "@vue/test-utils"
import { describe, expect, it } from "vitest"

import ResumePrintView from "../components/ResumePrintView.vue"
import type { ResumePayload } from "../lib/drafts"

const baseResume: ResumePayload = {
  version: 1,
  basic: { name: "张三", phone: "13800138000", email: "zhangsan@example.com", city: "上海" },
  job: { targetRole: "数据分析师", expectedSalary: "15k-20k", employmentType: "全职" },
  education: [
    { school: "某某大学", major: "计算机科学", degree: "本科", startDate: "2021-09", endDate: "2025-06" },
  ],
  employment: [
    { company: "示例科技", position: "数据实习生", startDate: "2024-01", endDate: "2024-06", description: "搭建转化漏斗看板" },
  ],
  projects: [
    { name: "电商用户行为分析", role: "数据分析", startDate: "2024-03", endDate: "2024-06", description: "分析 100 万条日志" },
  ],
  skills: { skills: ["SQL", "Python"], certificates: ["CET-6"] },
  selfEvaluation: "对数据敏感，喜欢用数据驱动决策",
  sectionVisibility: {
    basic: true, job: true, education: true, employment: true,
    projects: true, skills: true, selfEvaluation: true,
  },
}

describe("ResumePrintView", () => {
  it("renders every visible section with header, intent and contact lines", () => {
    const wrapper = mount(ResumePrintView, { props: { resume: baseResume } })
    const text = wrapper.text()
    expect(text).toContain("张三")
    expect(text).toContain("求职意向：数据分析师 · 15k-20k · 全职")
    expect(text).toContain("13800138000 · zhangsan@example.com · 上海")
    for (const heading of ["教育经历", "工作经历", "项目经历", "技能与证书", "自我评价"]) {
      expect(text).toContain(heading)
    }
    expect(text).toContain("某某大学")
    expect(text).toContain("SQL · Python")
    expect(text).toContain("2021-09 – 2025-06")
    expect(text).not.toContain("内容为空")
  })

  it("hides sections switched off by section visibility", () => {
    const resume: ResumePayload = {
      ...baseResume,
      sectionVisibility: {
        basic: true, job: true, education: false, employment: true,
        projects: false, skills: false, selfEvaluation: false,
      },
    }
    const wrapper = mount(ResumePrintView, { props: { resume } })
    const text = wrapper.text()
    expect(text).toContain("工作经历")
    expect(text).not.toContain("教育经历")
    expect(text).not.toContain("项目经历")
    expect(text).not.toContain("自我评价")
  })

  it("drops blank entries and shows the empty hint when nothing is printable", () => {
    const blank: ResumePayload = {
      ...baseResume,
      education: [{ school: "", major: "", degree: "", startDate: "", endDate: "" }],
      employment: [],
      projects: [],
      skills: { skills: [], certificates: [] },
      selfEvaluation: "  ",
    }
    const wrapper = mount(ResumePrintView, { props: { resume: blank } })
    const text = wrapper.text()
    expect(text).not.toContain("教育经历")
    expect(text).toContain("内容为空")
  })
})

describe("ResumeEditorView print fallback wiring", () => {
  it("falls back to browser printing when the cloud PDF renderer is unavailable", () => {
    const modulePath = resolve(process.cwd(), "src", "views", "ResumeEditorView.vue")
    expect(existsSync(modulePath)).toBe(true)
    const text = readFileSync(modulePath, "utf8")
    expect(text).toContain('caught.code === "pdf_renderer_unavailable"')
    expect(text).toContain("await openPrintPreview()")
    expect(text).toContain("ResumePrintView")
    expect(text).toContain("另存为 PDF")
  })
})
