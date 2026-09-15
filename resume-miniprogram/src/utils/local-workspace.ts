import type { Pinia } from "pinia"

import { useApplicationsStore } from "../stores/applications"
import { useAssessmentStore } from "../stores/assessment"
import { useCareerStore } from "../stores/career"
import { useConsultationStore } from "../stores/consultation"
import { useResumeStore } from "../stores/resume"
import { getAuthUser } from "../stores/session"

export function restoreLocalWorkspace(pinia?: Pinia): void {
  if (!getAuthUser()) return
  const resume = useResumeStore(pinia)
  const career = useCareerStore(pinia)
  const consultation = useConsultationStore(pinia)
  const applications = useApplicationsStore(pinia)
  const assessment = useAssessmentStore(pinia)
  resume.resetDraft(false)
  career.resetPlanner(false)
  consultation.resetConsultation(false)
  applications.pending = []
  assessment.resetAssessment()
  resume.restoreCheckpoint()
  career.restoreCheckpoint()
  consultation.restore()
  applications.restorePending()
}
