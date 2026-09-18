import { createApp } from "vue"

import App from "./App.vue"
import ErrorNotice from "./components/ErrorNotice.vue"
import "./styles/base.css"

/**
 * 启动失败兜底：若 Vue 尚未挂载成功（如老设备不支持某 API 导致整包解析失败），
 * 把错误显示在 index.html 的启动壳里——用户能直接截图反馈，而不是面对黑屏。
 */
function showBootError(reason: unknown): void {
  const shell = document.getElementById("boot-shell")
  const errorBox = document.getElementById("boot-error")
  if (!shell || !errorBox) return
  const detail = reason instanceof Error ? `${reason.name}: ${reason.message}` : String(reason)
  errorBox.textContent = `加载遇到问题，请截图反馈：${detail.slice(0, 160)}`
  errorBox.style.display = "block"
  const spinner = shell.querySelector<HTMLElement>(".boot-spinner")
  if (spinner) spinner.style.display = "none"
}

window.addEventListener("error", (event) => {
  if (!document.getElementById("boot-shell")) return
  showBootError(event.error ?? event.message)
})
window.addEventListener("unhandledrejection", (event) => {
  if (!document.getElementById("boot-shell")) return
  showBootError(event.reason)
})

createApp(App).component("ErrorNotice", ErrorNotice).mount("#app")
