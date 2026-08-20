import { createSSRApp } from "vue"
import { createPinia } from "pinia"

import App from "./App.vue"
import { installGlobalErrorHandler } from "./services/client-error-reporting"
import { useConsultationStore } from "./stores/consultation"
import { useResumeStore } from "./stores/resume"

export function createApp() {
  const app = createSSRApp(App)
  const pinia = createPinia()
  app.use(pinia)
  installGlobalErrorHandler(app)
  useResumeStore(pinia).restoreCheckpoint()
  useConsultationStore(pinia).restore()
  return { app }
}
