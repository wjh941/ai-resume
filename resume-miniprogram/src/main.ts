import { createSSRApp } from "vue"
import { createPinia } from "pinia"

import App from "./App.vue"
import { installGlobalErrorHandler } from "./services/client-error-reporting"
import { restoreLocalWorkspace } from "./utils/local-workspace"

export function createApp() {
  const app = createSSRApp(App)
  const pinia = createPinia()
  app.use(pinia)
  installGlobalErrorHandler(app)
  restoreLocalWorkspace(pinia)
  return { app }
}
