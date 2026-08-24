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
  <view class="ui-loading-spinner" :class="`ui-loading-spinner-${size}`" role="status" :aria-label="label">
    <view class="ui-loading-spinner-ring" aria-hidden="true" />
  </view>
</template>
