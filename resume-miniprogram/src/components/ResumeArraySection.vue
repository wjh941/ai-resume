<script setup lang="ts">
defineProps<{ title: string; emptyText: string }>()
defineEmits<{ add: []; remove: [index: number] }>()
</script>

<template>
  <view class="section">
    <view class="header"><text>{{ title }}</text><button size="mini" @click="$emit('add')">新增</button></view>
    <slot />
    <text class="empty" v-if="!$slots.default">{{ emptyText }}</text>
  </view>
</template>

<style scoped>
.section { margin: 28rpx 0; padding: 20rpx; border-radius: 16rpx; background: #fff; }
.header { display: flex; justify-content: space-between; align-items: center; font-weight: 600; }
.empty { display: block; margin-top: 16rpx; color: #86909c; font-size: 24rpx; }
</style>
