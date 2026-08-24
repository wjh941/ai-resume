import { computed, ref, type Ref } from "vue"

export function useIncrementalList<T>(
  source: Readonly<Ref<readonly T[]>>,
  initial = 40,
  step = 40,
) {
  const limit = ref(initial)
  const visibleItems = computed(() => source.value.slice(0, limit.value))
  const hasMore = computed(() => limit.value < source.value.length)

  function showMore(): void {
    limit.value = Math.min(limit.value + step, source.value.length)
  }

  function reset(): void {
    limit.value = initial
  }

  return { visibleItems, hasMore, showMore, reset }
}
