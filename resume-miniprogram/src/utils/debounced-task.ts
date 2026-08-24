export type DebouncedTask = {
  schedule(): void
  flush(): void
  cancel(): void
  isPending(): boolean
}

export function createDebouncedTask(action: () => void, delayMs: number): DebouncedTask {
  let timer: ReturnType<typeof setTimeout> | null = null

  const cancel = () => {
    if (timer === null) return
    clearTimeout(timer)
    timer = null
  }

  const run = () => {
    timer = null
    action()
  }

  return {
    schedule() {
      cancel()
      timer = setTimeout(run, delayMs)
    },
    flush() {
      if (timer === null) return
      cancel()
      action()
    },
    cancel,
    isPending: () => timer !== null,
  }
}
