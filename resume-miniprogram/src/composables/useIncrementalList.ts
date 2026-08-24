import { computed, ref, type Ref } from "vue"

export function useIncrementalList<T>(
  source: Readonly<Ref<readonly T[]>>,
  initial = 20,
  step = 20,
) {
  const limit = ref(initial)
  const visibleItems = computed(() => source.value.slice(0, limit.value))
  const hasMore = computed(() => limit.value < source.value.length)
  const showMore = () => { limit.value = Math.min(limit.value + step, source.value.length) }
  const reset = () => { limit.value = initial }
  return { visibleItems, hasMore, showMore, reset }
}
