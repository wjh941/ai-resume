import { computed, onScopeDispose, ref, type Ref } from "vue"

export type StagedProgress = {
  /** 是否处于推进状态。 */
  active: Ref<boolean>
  /** 当前阶段文案（超出阶段数时停在最后一条）。 */
  label: Ref<string>
  /** 已等待秒数（整秒递增）。 */
  elapsedSeconds: Ref<number>
  start: () => void
  stop: () => void
}

/**
 * AI 长任务（30-90 秒）的阶段化等待提示：定时推进阶段文案并累计等待秒数，
 * 让用户知道“系统在动”，而不是面对一个不知何时结束的转圈。
 */
export function createStagedProgress(stages: readonly string[], intervalMs = 12_000): StagedProgress {
  const active = ref(false)
  const stageIndex = ref(0)
  const elapsedSeconds = ref(0)
  let stageTimer: ReturnType<typeof setInterval> | null = null
  let tickTimer: ReturnType<typeof setInterval> | null = null

  function clearTimers(): void {
    if (stageTimer !== null) { clearInterval(stageTimer); stageTimer = null }
    if (tickTimer !== null) { clearInterval(tickTimer); tickTimer = null }
  }

  function stop(): void {
    active.value = false
    clearTimers()
  }

  function start(): void {
    stop()
    active.value = true
    stageIndex.value = 0
    elapsedSeconds.value = 0
    if (stages.length > 1) {
      stageTimer = setInterval(() => {
        stageIndex.value = Math.min(stageIndex.value + 1, stages.length - 1)
      }, intervalMs)
    }
    tickTimer = setInterval(() => { elapsedSeconds.value += 1 }, 1_000)
  }

  try {
    onScopeDispose(stop)
  } catch {
    // 组件作用域之外使用时忽略
  }

  const label = computed(() => stages[Math.min(stageIndex.value, stages.length - 1)] ?? "")
  return { active, label, elapsedSeconds, start, stop }
}
