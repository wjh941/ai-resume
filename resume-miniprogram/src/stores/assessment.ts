import { defineStore } from "pinia"

import type {
  AnnualInsight,
  AssessmentQuestion,
  SavedAssessment,
} from "../types/assessment"

export const useAssessmentStore = defineStore("career-assessment", {
  state: () => ({
    questions: [] as AssessmentQuestion[],
    notice: "",
    answers: {} as Record<string, number>,
    result: null as SavedAssessment | null,
    insights: [] as AnnualInsight[],
  }),
  actions: {
    setQuestions(questions: AssessmentQuestion[], notice: string): void {
      this.questions = questions
      this.notice = notice
    },
    answer(key: string, value: number): void {
      this.answers[key] = value
    },
    setResult(result: SavedAssessment): void {
      this.answers = { ...result.answers }
      this.result = result
    },
    setInsights(insights: AnnualInsight[]): void {
      this.insights = insights
    },
  },
})
