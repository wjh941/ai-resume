import { ref } from "vue"

export function useAsyncAction() {
  const pending = ref(false)

  async function run<T>(operation: () => Promise<T>): Promise<T | undefined> {
    if (pending.value) return undefined
    pending.value = true
    try {
      return await operation()
    } finally {
      pending.value = false
    }
  }

  return { pending, run }
}
