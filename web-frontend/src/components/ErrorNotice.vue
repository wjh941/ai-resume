<script setup lang="ts">
withDefaults(defineProps<{
  message: string
  compact?: boolean
}>(), {
  compact: false,
})
</script>

<template>
  <p class="notice-error" :class="{ 'notice-error--compact': compact, 'notice-with-action': Boolean($slots.default) }" role="alert" aria-live="assertive">
    <span class="notice-error-message">{{ message }}</span>
    <span v-if="$slots.default" class="notice-error-actions"><slot /></span>
  </p>
</template>
