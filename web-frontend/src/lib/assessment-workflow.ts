import type { AssessmentQuestion, AssessmentReport } from "./assessment"

export function isAssessmentComplete(questions: AssessmentQuestion[], answers: Record<string, number>): boolean {
  return questions.length > 0 && questions.every((question) => Number.isInteger(answers[question.key]))
}

export function mergeAssessmentAnswers(current: Record<string, number>, saved: Record<string, number>): Record<string, number> {
  return { ...current, ...saved }
}

export function flattenActionPlan(report: AssessmentReport): string[] {
  return [...report.actionPlan.sevenDay, ...report.actionPlan.thirtyDay, ...report.actionPlan.ninetyDay]
}
