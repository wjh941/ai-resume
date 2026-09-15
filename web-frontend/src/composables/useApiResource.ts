import { getCurrentInstance, onMounted, onUnmounted, ref, type Ref } from "vue"

import { getApiErrorMessage } from "../lib/api-error"

export type UseApiResourceOptions = {
  /** 请求失败且无法归类时的兜底文案（超时 / 401 / 403 / 网络错误仍走共享映射）。 */
  fallbackMessage?: string
  /** 为 true 时在 onMounted 自动触发一次加载，等价于旧视图的 onMounted(refresh)。 */
  immediate?: boolean
}

export type UseApiResourceReturn<T> = {
  data: Ref<T | null>
  loading: Ref<boolean>
  error: Ref<string | null>
  run: () => Promise<void>
  retry: () => Promise<void>
  /** 是否存在可重试的上一次失败（对应旧视图的 retryAction 非空，用于重试按钮显隐）。 */
  retryable: Ref<boolean>
  /** 其他操作开始时清除可重试状态，等价于旧视图的 retryAction.value = null。 */
  clearRetry: () => void
}

const defaultFallbackMessage = "加载失败，请稍后重试"

export function useApiResource<T>(
  loader: () => Promise<T>,
  options: UseApiResourceOptions = {},
): UseApiResourceReturn<T> {
  const fallbackMessage = options.fallbackMessage ?? defaultFallbackMessage
  const data = ref(null) as Ref<T | null>
  const loading = ref(options.immediate === true)
  const error = ref<string | null>(null)
  const retryable = ref(false)
  let requestSeq = 0
  let disposed = false

  if (getCurrentInstance()) {
    onUnmounted(() => {
      disposed = true
    })
    if (options.immediate) {
      onMounted(() => {
        void run()
      })
    }
  }

  function clearRetry(): void {
    retryable.value = false
  }

  async function run(): Promise<void> {
    // requestId 守卫：以最新一次调用为准，过期的慢响应不会覆盖新状态。
    const requestId = ++requestSeq
    retryable.value = false
    loading.value = true
    error.value = null
    try {
      const result = await loader()
      if (disposed || requestId !== requestSeq) return
      data.value = result
    } catch (reason) {
      if (disposed || requestId !== requestSeq) return
      error.value = getApiErrorMessage(reason, fallbackMessage)
      retryable.value = true
    } finally {
      if (!disposed && requestId === requestSeq) loading.value = false
    }
  }

  async function retry(): Promise<void> {
    if (!retryable.value) return
    await run()
  }

  return { data, loading, error, run, retry, retryable, clearRetry }
}
