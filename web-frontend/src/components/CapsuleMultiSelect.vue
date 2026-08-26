<script setup lang="ts">
import { Check } from "lucide-vue-next"
import { computed, onBeforeUnmount, ref, watch } from "vue"

import AsyncButton from "./AsyncButton.vue"
import { toggleComparisonRole } from "../lib/comparison-workflow"

const props = withDefaults(defineProps<{
  options: string[]
  selected: string[]
  maxSelectable?: number
  pending?: boolean
  loading?: boolean
  skeletonCount?: number
  success?: boolean
}>(), { maxSelectable: 4, pending: false, loading: false, skeletonCount: 6, success: false })

const emit = defineEmits<{ "update:selected": [value: string[]]; submit: [] }>()
const settlingRole = ref("")
const percent = ref(0)
const bursting = ref(false)
let settleTimer: ReturnType<typeof setTimeout> | undefined
let burstTimer: ReturnType<typeof setTimeout> | undefined
let frame = 0

const targetPercent = computed(() => props.options.length
  ? Math.round((props.selected.length / Math.min(props.maxSelectable, props.options.length)) * 100)
  : 0)
const skeletonLabels = computed(() => {
  const labels = props.options.length ? props.options : ["岗位标签", "目标方向", "技能匹配", "工作场景", "发展路径", "优先选择"]
  return Array.from({ length: props.skeletonCount }, (_, index) => labels[index % labels.length])
})

function capturePointer(event: PointerEvent): void {
  const target = event.currentTarget as HTMLElement | null
  if (!target) return
  const rect = target.getBoundingClientRect()
  target.style.setProperty("--ripple-x", `${event.clientX - rect.left}px`)
  target.style.setProperty("--ripple-y", `${event.clientY - rect.top}px`)
}

function settle(role: string): void {
  settlingRole.value = role
  if (settleTimer) clearTimeout(settleTimer)
  settleTimer = setTimeout(() => { if (settlingRole.value === role) settlingRole.value = "" }, 380)
}

function toggle(role: string): void {
  if (props.pending || props.loading) return
  emit("update:selected", toggleComparisonRole(props.selected, role, props.maxSelectable))
  settle(role)
}

function selectAll(): void {
  if (props.pending || props.loading) return
  emit("update:selected", props.options.slice(0, props.maxSelectable))
  settle("__all__")
}

function reset(): void {
  if (props.pending || props.loading) return
  emit("update:selected", [])
  settle("__reset__")
}

function animatePercent(next: number): void {
  if (typeof window === "undefined") { percent.value = next; return }
  if (frame) window.cancelAnimationFrame(frame)
  const from = percent.value
  const start = performance.now()
  const tick = (now: number) => {
    const progress = Math.min(1, (now - start) / 560)
    const eased = 1 - Math.pow(1 - progress, 3)
    percent.value = Math.round(from + (next - from) * eased)
    if (progress < 1) frame = window.requestAnimationFrame(tick)
    else frame = 0
  }
  frame = window.requestAnimationFrame(tick)
}

function triggerBurst(): void {
  if (typeof window === "undefined") return
  bursting.value = false
  window.requestAnimationFrame(() => {
    bursting.value = true
    if (burstTimer) clearTimeout(burstTimer)
    burstTimer = setTimeout(() => { bursting.value = false }, 700)
  })
}

watch(targetPercent, animatePercent, { immediate: true })
watch(() => props.success, (value) => { if (value) triggerBurst() })
onBeforeUnmount(() => {
  if (settleTimer) clearTimeout(settleTimer)
  if (burstTimer) clearTimeout(burstTimer)
  if (frame && typeof window !== "undefined") window.cancelAnimationFrame(frame)
})
</script>

<template>
  <section class="capsule-multi-select" :aria-busy="loading || pending">
    <div v-if="!loading" class="capsule-toolbar">
      <button class="capsule-elastic" :class="{ 'is-elastic-active': settlingRole === '__all__' }" type="button" :disabled="pending" @click="selectAll">全选</button>
      <button class="capsule-elastic capsule-elastic-muted" :class="{ 'is-elastic-active': settlingRole === '__reset__' }" type="button" :disabled="pending" @click="reset">重置</button>
    </div>
    <div class="role-chip-grid capsule-tag-grid">
      <Transition name="capsule-skeleton" mode="out-in">
        <div v-if="loading" class="capsule-tag-grid-inner">
          <span v-for="label in skeletonLabels" :key="label" class="capsule-tag capsule-tag-skeleton" aria-hidden="true"><span class="capsule-tag-inner"><span class="capsule-tag-face capsule-tag-front">{{ label }}</span></span></span>
        </div>
        <div v-else class="capsule-tag-grid-inner">
          <button v-for="role in options" :key="role" class="capsule-tag" :class="{ 'is-selected': selected.includes(role), 'is-settling': settlingRole === role }" type="button" :disabled="pending" :aria-pressed="selected.includes(role)" @pointerdown="capturePointer" @click="toggle(role)">
            <span class="capsule-tag-inner"><span class="capsule-tag-face capsule-tag-front">{{ role }}</span><span class="capsule-tag-face capsule-tag-back" aria-hidden="true">点击切换</span></span>
            <Transition name="capsule-check"><span v-if="selected.includes(role)" class="capsule-tag-check" aria-hidden="true"><Check :size="13" stroke-width="2.8" /></span></Transition>
          </button>
        </div>
      </Transition>
    </div>
    <div class="capsule-progress-row" aria-live="polite"><span>匹配进度</span><strong>{{ percent }}%</strong><span class="capsule-progress-track" aria-hidden="true"><span class="capsule-progress-fill" :style="{ '--progress-scale': percent / 100 }" /></span></div>
    <AsyncButton class="primary-button compact capsule-submit" :class="{ 'particle-burst': bursting }" type="button" :loading="pending" :disabled="selected.length < 2 || selected.length > maxSelectable" @click="emit('submit')">
      <span class="capsule-particle-layer" aria-hidden="true"><i v-for="index in 8" :key="index" class="capsule-particle" :style="{ '--particle-index': index }" /></span>
      <span>开始对比</span>
    </AsyncButton>
  </section>
</template>
