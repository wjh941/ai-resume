import { createSSRApp } from "vue"
import { createPinia } from "pinia"

import App from "./App.vue"
import { useResumeStore } from "./stores/resume"

export function createApp() {
  const app = createSSRApp(App)
  const pinia = createPinia()
  app.use(pinia)
  useResumeStore(pinia).restoreCheckpoint()
  return { app }
}
