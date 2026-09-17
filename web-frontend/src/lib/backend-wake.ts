import { onScopeDispose, ref, type Ref } from "vue"

export type WakeProbe = () => Promise<boolean>

export type BackendWakeMonitor = {
  /** 后端尚未探活成功（处于冷启动或不可达状态）。 */
  waking: Ref<boolean>
  /** 已执行的探测次数（用于界面提示“第 N 次重试”）。 */
  attempts: Ref<number>
  /** 最近一次探测的错误摘要，用于横幅提示。 */
  lastError: Ref<string>
  /** 立即探测一次；成功会停止循环并清除 waking。 */
  probe: () => Promise<boolean>
}

export type BackendWakeOptions = {
  requestFn: WakeProbe
  intervalMs?: number
  maxAttempts?: number
  /** 由调用方决定轮询生命周期（如 App 卸载时停止）；默认随当前组件作用域自动停止。 */
  autoStop?: boolean
}

/**
 * 免费托管冷启动监测：应用启动即探活 /health，失败时按固定间隔重试，
 * 界面据此显示“服务唤醒中”而不是让每个请求各自超时报错。
 */
export function createBackendWakeMonitor(options: BackendWakeOptions): BackendWakeMonitor {
  const intervalMs = options.intervalMs ?? 6_000
  const maxAttempts = options.maxAttempts ?? 15
  const waking: Ref<boolean> = ref(true)
  const attempts = ref(0)
  const lastError = ref("")
  let timer: ReturnType<typeof setTimeout> | null = null
  let stopped = false

  function stop(): void {
    stopped = true
    if (timer !== null) {
      clearTimeout(timer)
      timer = null
    }
  }

  async function probe(): Promise<boolean> {
    if (stopped) return false
    attempts.value += 1
    try {
      const healthy = await options.requestFn()
      if (healthy) {
        waking.value = false
        lastError.value = ""
        stop()
        return true
      }
      lastError.value = "服务暂未就绪"
    } catch (reason) {
      lastError.value = reason instanceof Error && reason.message ? reason.message : "探测失败"
    }
    if (!stopped && attempts.value < maxAttempts && timer === null) {
      timer = setTimeout(() => {
        timer = null
        void probe()
      }, intervalMs)
    }
    return false
  }

  if (options.autoStop !== false && typeof onScopeDispose === "function") {
    try {
      onScopeDispose(stop)
    } catch {
      // 在组件作用域之外使用时忽略
    }
  }

  return { waking, attempts, lastError, probe }
}
