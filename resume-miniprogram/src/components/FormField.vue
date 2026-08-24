<script setup lang="ts">
import { getCurrentInstance } from "vue"

defineProps<{ label: string; modelValue: string; placeholder?: string; error?: string }>()
defineEmits<{ "update:modelValue": [value: string] }>()

const fieldId = `form-field-${getCurrentInstance()?.uid ?? 0}`
const errorId = `${fieldId}-error`
</script>

<template>
  <view class="field">
    <text class="label">{{ label }}</text>
    <input
      :id="fieldId"
      :class="{ invalid: error }"
      :value="modelValue"
      :placeholder="placeholder"
      :aria-label="label"
      :aria-invalid="Boolean(error)"
      :aria-describedby="error ? errorId : undefined"
      @input="$emit('update:modelValue', $event.detail.value)"
    />
    <text v-if="error" :id="errorId" class="ui-error-tip ui-error-tip--inline" role="alert">{{ error }}</text>
  </view>
</template>

<style scoped>
.field { margin: 20rpx 0; }
.label { display: block; margin-bottom: 10rpx; color: #4e5969; font-size: 24rpx; }
input { min-height: 76rpx; padding: 0 20rpx; background: #fff; border: 1px solid #e5e6eb; border-radius: 12rpx; }.invalid { border-color: #d4380d; background: #fff7f0; }.error { display: block; margin-top: 8rpx; color: #d4380d; font-size: 22rpx; line-height: 1.4; }
</style>
