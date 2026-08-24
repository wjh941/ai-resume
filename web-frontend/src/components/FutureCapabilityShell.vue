<script setup lang="ts">
withDefaults(defineProps<{
  title: string
  description: string
}>(), {
  title: "即将开放",
  description: "相关能力正在准备中。",
})
</script>

<template>
  <section class="future-capability-shell" aria-live="polite">
    <span class="future-capability-mark" aria-hidden="true" />
    <div>
      <h2>{{ title }}</h2>
      <p>{{ description }}</p>
      <div v-if="$slots.default" class="future-capability-actions"><slot /></div>
    </div>
  </section>
</template>
