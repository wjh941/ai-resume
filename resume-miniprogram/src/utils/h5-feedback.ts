const MISSING_ROLE_ERROR = "请输入岗位名称，或从下方联想岗位中选择。"
const UNANSWERED_STEP_HINT = "本步骤尚未作答，可继续并稍后补充"

export function getRoleFieldError(roles: readonly string[]): string {
  return roles.length ? "" : MISSING_ROLE_ERROR
}

export function getAssessmentStepTransition(
  currentStep: number,
  stepCount: number,
  hasAnswer: boolean,
): { stepHint: string; nextStep: number; shouldSubmit: boolean } {
  const shouldSubmit = currentStep >= stepCount - 1
  return {
    stepHint: hasAnswer ? "" : UNANSWERED_STEP_HINT,
    nextStep: shouldSubmit ? currentStep : currentStep + 1,
    shouldSubmit,
  }
}
