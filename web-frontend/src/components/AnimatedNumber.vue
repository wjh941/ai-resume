<script setup lang="ts">
defineProps<{
  value: number | string
}>()
</script>

<template>
  <span :key="String(value)" class="animated-number">{{ value }}</span>
</template>
