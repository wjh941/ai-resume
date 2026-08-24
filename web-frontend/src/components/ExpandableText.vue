<script setup lang="ts">
import { computed, ref, useId, watch } from "vue"

import { isExpandableText } from "../lib/expandable-text"

const props = withDefaults(defineProps<{
  text: string
  lines?: 1 | 4
  expandAt?: number
  label?: string
}>(), {
  lines: 4,
  expandAt: 96,
  label: "完整内容",
})

const expanded = ref(false)
const contentId = `expandable-${useId().replace(/:/g, "")}`
const expandable = computed(() => isExpandableText(props.text, props.expandAt))

watch(() => props.text, () => {
  expanded.value = false
})
</script>

<template>
  <span class="expandable-text" :class="`is-${lines}-line`">
    <span
      :id="contentId"
      class="expandable-copy"
      :class="{ 'is-collapsed': expandable && !expanded }"
    >{{ text }}</span>
    <button
      v-if="expandable"
      type="button"
      class="expandable-toggle"
      :aria-controls="contentId"
      :aria-expanded="expanded"
      :aria-label="`${expanded ? '收起' : '展开'}${label}`"
      @click="expanded = !expanded"
    >{{ expanded ? "收起" : "展开" }}</button>
  </span>
</template>
