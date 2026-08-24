<script setup lang="ts">
import { computed, getCurrentInstance, ref, watch } from "vue"

import { isExpandableText } from "../utils/expandable-text"

const props = withDefaults(defineProps<{
  text: string
  lines?: 1 | 4
  expandAt?: number
  label?: string
}>(), {
  lines: 4,
  expandAt: 96,
  label: "内容",
})

const expanded = ref(false)
const contentId = `expandable-text-${getCurrentInstance()?.uid ?? 0}`
const canExpand = computed(() => isExpandableText(props.text, props.expandAt))
const toggleLabel = computed(() => `${expanded.value ? "收起" : "展开"}${props.label}`)

watch(() => props.text, () => {
  expanded.value = false
})
</script>

<template>
  <view class="expandable-text">
    <text
      :id="contentId"
      class="expandable-copy"
      :class="{ 'is-collapsed': canExpand && !expanded }"
      :style="{ '--expandable-lines': String(lines) }"
    >{{ text }}</text>
    <button
      v-if="canExpand"
      size="mini"
      class="expandable-toggle"
      :aria-controls="contentId"
      :aria-expanded="expanded"
      :aria-label="toggleLabel"
      @click="expanded = !expanded"
    >{{ expanded ? "收起" : "展开" }}</button>
  </view>
</template>

<style scoped>
.expandable-text { display: block; min-width: 0; max-width: 100%; }
.expandable-copy { display: block; max-width: 100%; overflow-wrap: anywhere; }
.expandable-copy.is-collapsed { display: -webkit-box; overflow: hidden; -webkit-box-orient: vertical; -webkit-line-clamp: var(--expandable-lines); overflow-wrap: anywhere; }
.expandable-toggle { width: auto; min-height: 48rpx; margin: 6rpx 0 0; padding: 0 4rpx; color: #1677ff; background: transparent; border: 0; font-size: 22rpx; line-height: 48rpx; text-align: left; }
.expandable-toggle::after { border: 0; }
</style>
