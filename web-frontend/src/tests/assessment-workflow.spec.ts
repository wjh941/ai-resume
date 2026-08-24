import { describe, expect, it } from "vitest"

import {
  ASSESSMENT_INCOMPLETE_ERROR,
  clearAssessmentValidationError,
  flattenActionPlan,
  isAssessmentComplete,
  mergeAssessmentAnswers,
  resolveAssessmentSubmitAction,
} from "../lib/assessment-workflow"
import type { AssessmentQuestion, AssessmentReport } from "../lib/assessment"

const questions: AssessmentQuestion[] = [{ key: "q1", group: "interest", dimension: "analysis", title: "题目" }, { key: "q2", group: "constraints", dimension: "time", title: "题目二" }]
const report: AssessmentReport = { topInterests: [], workStyleSummary: "", strengthEvidence: [], confidenceNote: "", answeredCount: 2, actionPlan: { sevenDay: ["七天"], thirtyDay: ["三十天"], ninetyDay: ["九十天"] } }

describe("assessment workflow helpers", () => {
  it("requires every question before submission", () => {
    expect(isAssessmentComplete(questions, { q1: 4 })).toBe(false)
    expect(isAssessmentComplete(questions, { q1: 4, q2: 2 })).toBe(true)
  })

  it("preserves local answers while merging a saved result", () => {
    expect(mergeAssessmentAnswers({ q1: 4 }, { q2: 3 })).toEqual({ q1: 4, q2: 3 })
  })

  it("keeps the three action-plan horizons in order", () => {
    expect(flattenActionPlan(report)).toEqual(["七天", "三十天", "九十天"])
  })

  it("blocks incomplete and duplicate submissions before the API boundary", () => {
    expect(resolveAssessmentSubmitAction(false, false)).toBe("show-validation")
    expect(resolveAssessmentSubmitAction(true, true)).toBe("ignore")
    expect(resolveAssessmentSubmitAction(true, false)).toBe("submit")
  })

  it("clears only the local incomplete-form error after all answers are supplied", () => {
    expect(clearAssessmentValidationError(true, ASSESSMENT_INCOMPLETE_ERROR)).toBe("")
    expect(clearAssessmentValidationError(true, "测评服务暂不可用")).toBe("测评服务暂不可用")
    expect(clearAssessmentValidationError(false, ASSESSMENT_INCOMPLETE_ERROR)).toBe(ASSESSMENT_INCOMPLETE_ERROR)
  })
})
