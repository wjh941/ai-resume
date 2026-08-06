<script setup lang="ts">
defineProps<{ label: string; modelValue: string; placeholder?: string }>()
defineEmits<{ "update:modelValue": [value: string] }>()
</script>

<template>
  <view class="field">
    <text class="label">{{ label }}</text>
    <input :value="modelValue" :placeholder="placeholder" @input="$emit('update:modelValue', $event.detail.value)" />
  </view>
</template>

<style scoped>
.field { margin: 20rpx 0; }
.label { display: block; margin-bottom: 10rpx; color: #4e5969; font-size: 24rpx; }
input { min-height: 76rpx; padding: 0 20rpx; background: #fff; border: 1px solid #e5e6eb; border-radius: 12rpx; }
</style>
