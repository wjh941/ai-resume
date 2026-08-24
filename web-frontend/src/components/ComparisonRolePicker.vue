<script setup lang="ts">
import AsyncButton from "./AsyncButton.vue"
import { toggleComparisonRole } from "../lib/comparison-workflow"

defineProps<{ roles: string[]; selected: string[]; maxSelectable: number }>()
const emit = defineEmits<{ "update:selected": [value: string[]]; submit: [] }>()

function toggle(role: string, selected: string[]): void {
  const next = toggleComparisonRole(selected, role, 4)
  emit("update:selected", next)
}
</script>

<template>
  <section class="comparison-picker"><div class="panel-heading"><div><span class="section-kicker">岗位选择</span><h2>选择 2–4 个岗位</h2></div><span class="toolbar-hint">已选 {{ selected.length }} / {{ maxSelectable }}</span></div><div class="role-chip-grid"><button v-for="role in roles" :key="role" type="button" :class="{ 'is-selected': selected.includes(role) }" :aria-pressed="selected.includes(role)" @click="toggle(role, selected)">{{ role }}</button></div><AsyncButton class="primary-button compact" type="button" :disabled="selected.length < 2 || selected.length > maxSelectable" @click="emit('submit')">开始对比</AsyncButton></section>
</template>
