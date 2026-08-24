<script setup lang="ts">
import { computed } from "vue"

import type { AssessmentQuestion } from "../lib/assessment"

const props = defineProps<{
  question: AssessmentQuestion
  modelValue: number | undefined
  disabled: boolean
  invalid?: boolean
}>()

const emit = defineEmits<{ "update:modelValue": [value: number] }>()
const hintId = computed(() => `assessment-question-${props.question.key}-error`)
</script>

<template>
  <article class="assessment-question" :class="{ 'is-invalid': invalid }" :aria-invalid="invalid || undefined" :aria-describedby="invalid ? hintId : undefined"><span class="question-group">{{ question.group === "work_style" ? "工作方式" : question.group === "strength_evidence" ? "优势线索" : question.group === "constraints" ? "现实约束" : "兴趣方向" }}</span><h3>{{ question.title }}</h3><div class="answer-scale" role="radiogroup" :aria-label="question.title"><button v-for="value in 5" :key="value" type="button" :class="{ 'is-selected': modelValue === value }" :disabled="disabled" :aria-pressed="modelValue === value" @click="emit('update:modelValue', value)">{{ value }}</button></div><div class="scale-hint"><span>不符合</span><span>非常符合</span></div><small v-if="invalid" :id="hintId" class="question-error">请选择一个符合程度</small></article>
</template>
