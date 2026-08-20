<script setup lang="ts">
function returnToWorkspace(): void {
  uni.reLaunch({ url: "/pages/job-search/index" })
}

function returnToAccount(): void {
  uni.reLaunch({ url: "/pages/account/index" })
}
</script>

<template>
  <view class="page">
    <view class="content">
      <text class="title">页面暂时无法加载</text>
      <text class="copy">刚才的操作没有展示技术错误信息。你可以返回工作台继续操作，或前往账户中心重新登录。</text>
      <button class="primary" @click="returnToWorkspace">返回工作台</button>
      <button class="secondary" @click="returnToAccount">前往账户中心</button>
    </view>
  </view>
</template>

<style scoped>
.page { display: flex; min-height: 100vh; box-sizing: border-box; padding: 40rpx 28rpx; align-items: center; background: #f4f7fb; }.content { width: 100%; padding: 36rpx 30rpx; box-sizing: border-box; text-align: center; background: #fff; border: 1rpx solid #e1eaf4; border-radius: 20rpx; box-shadow: 0 12rpx 30rpx rgba(35, 78, 130, .09); }.title,.copy { display: block; }.title { color: #1f2937; font-size: 38rpx; font-weight: 700; }.copy { margin-top: 16rpx; color: #64748b; font-size: 25rpx; line-height: 1.65; }.primary,.secondary { margin-top: 24rpx; }.primary { color: #fff; background: #1677ff; }.secondary { color: #245b99; background: #edf6ff; border: 1rpx solid #cfe4fb; }
</style>
