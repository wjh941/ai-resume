<script setup lang="ts">
import LoadingSpinner from "./LoadingSpinner.vue"

withDefaults(defineProps<{
  loading?: boolean
  disabled?: boolean
  type?: "button" | "submit" | "reset"
}>(), {
  loading: false,
  disabled: false,
  type: "button",
})
</script>

<template>
  <button
    v-bind="$attrs"
    :type="type"
    :disabled="disabled || loading"
    :aria-busy="loading || undefined"
    class="async-button"
    :class="{ 'is-loading': loading }"
  >
    <span class="async-button-spinner" aria-hidden="true">
      <LoadingSpinner v-if="loading" size="sm" aria-hidden="true" />
    </span>
    <span class="async-button-label"><slot /></span>
  </button>
</template>
