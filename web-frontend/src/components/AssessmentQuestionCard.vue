<script setup lang="ts">
import type { AssessmentQuestion } from "../lib/assessment"

defineProps<{
  question: AssessmentQuestion
  modelValue: number | undefined
  disabled: boolean
}>()

const emit = defineEmits<{ "update:modelValue": [value: number] }>()
</script>

<template>
  <article class="assessment-question"><span class="question-group">{{ question.group === "work_style" ? "工作方式" : question.group === "strength_evidence" ? "优势线索" : question.group === "constraints" ? "现实约束" : "兴趣方向" }}</span><h3>{{ question.title }}</h3><div class="answer-scale" role="radiogroup" :aria-label="question.title"><button v-for="value in 5" :key="value" type="button" :class="{ 'is-selected': modelValue === value }" :disabled="disabled" :aria-pressed="modelValue === value" @click="emit('update:modelValue', value)">{{ value }}</button></div><div class="scale-hint"><span>不符合</span><span>非常符合</span></div></article>
</template>
