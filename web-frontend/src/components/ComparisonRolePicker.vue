<script setup lang="ts">
import CapsuleMultiSelect from "./CapsuleMultiSelect.vue"

withDefaults(defineProps<{
  roles: string[]
  selected: string[]
  maxSelectable: number
  pending?: boolean
  loading?: boolean
  success?: boolean
}>(), { pending: false, loading: false, success: false })

const emit = defineEmits<{ "update:selected": [value: string[]]; submit: [] }>()
</script>

<template>
  <section class="comparison-picker">
    <div class="panel-heading">
      <div><span class="section-kicker">岗位选择</span><h2>选择 2–4 个岗位</h2></div>
      <span class="toolbar-hint">已选 {{ selected.length }} / {{ maxSelectable }}</span>
    </div>
    <CapsuleMultiSelect
      :options="roles"
      :selected="selected"
      :max-selectable="maxSelectable"
      :pending="pending"
      :loading="loading"
      :success="success"
      @update:selected="emit('update:selected', $event)"
      @submit="emit('submit')"
    />
  </section>
</template>
