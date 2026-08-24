<script setup lang="ts">
withDefaults(defineProps<{
  size?: "sm" | "md" | "lg"
  label?: string
}>(), {
  size: "md",
  label: "加载中",
})
</script>

<template>
  <span class="loading-spinner" :class="`loading-spinner-${size}`" role="status" :aria-label="label">
    <span class="loading-spinner-ring" aria-hidden="true" />
  </span>
</template>
