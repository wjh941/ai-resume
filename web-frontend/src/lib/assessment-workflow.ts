import type { AssessmentQuestion, AssessmentReport } from "./assessment"

export const ASSESSMENT_INCOMPLETE_ERROR = "请完成全部题目后提交"
export type AssessmentSubmitAction = "show-validation" | "ignore" | "submit"

export function isAssessmentComplete(questions: AssessmentQuestion[], answers: Record<string, number>): boolean {
  return questions.length > 0 && questions.every((question) => Number.isInteger(answers[question.key]))
}

export function mergeAssessmentAnswers(current: Record<string, number>, saved: Record<string, number>): Record<string, number> {
  return { ...current, ...saved }
}

export function flattenActionPlan(report: AssessmentReport): string[] {
  return [...report.actionPlan.sevenDay, ...report.actionPlan.thirtyDay, ...report.actionPlan.ninetyDay]
}

export function resolveAssessmentSubmitAction(complete: boolean, saving: boolean): AssessmentSubmitAction {
  if (!complete) return "show-validation"
  return saving ? "ignore" : "submit"
}

export function clearAssessmentValidationError(complete: boolean, error: string): string {
  return complete && error === ASSESSMENT_INCOMPLETE_ERROR ? "" : error
}
