<script setup lang="ts">
import { onBeforeUnmount, ref, watch } from "vue"

defineProps<{ hasMore: boolean }>()
const emit = defineEmits<{ more: [] }>()
const target = ref<HTMLButtonElement | null>(null)
let observer: IntersectionObserver | null = null

function disconnect(): void {
  observer?.disconnect()
  observer = null
}

watch(target, (element) => {
  disconnect()
  if (!("IntersectionObserver" in window) || !element) return

  observer = new IntersectionObserver(([entry]) => {
    if (entry?.isIntersecting) emit("more")
  }, { rootMargin: "240px 0px" })
  observer.observe(element)
}, { flush: "post" })

onBeforeUnmount(disconnect)
</script>

<template>
  <button v-if="hasMore" ref="target" type="button" class="progressive-list-sentinel" @click="emit('more')">显示更多</button>
</template>
