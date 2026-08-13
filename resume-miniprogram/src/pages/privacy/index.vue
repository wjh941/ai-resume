<script setup lang="ts">
import { useCareerStore } from "../../stores/career"
import { useConsultationStore } from "../../stores/consultation"
import { useResumeStore } from "../../stores/resume"
import { clearLocalCareerWorkspace } from "../../utils/local-privacy"

const resumeStore = useResumeStore()
const careerStore = useCareerStore()
const consultationStore = useConsultationStore()

function clearLocalData(): void {
  uni.showModal({
    title: "Clear local workspace",
    content: "This clears local checkpoints and pending tracker entries from this device.",
    success: (result) => {
      if (!result.confirm) return
      clearLocalCareerWorkspace()
      resumeStore.resetDraft(false)
      careerStore.resetPlanner(false)
      consultationStore.resetConsultation(false)
      uni.showToast({ title: "Local workspace cleared", icon: "success" })
    },
  })
}
</script>

<template>
  <scroll-view class="page" scroll-y>
    <text class="title">Local privacy</text>
    <view class="section">
      <text class="section-title">Clear this device</text>
      <text class="description">Remove locally stored resume checkpoints, career planning state, consultation state, assessment state, and pending tracker entries.</text>
      <button class="danger" @click="clearLocalData">Clear local workspace</button>
    </view>
    <view class="section">
      <text class="section-title">Server records</text>
      <text class="description">Server drafts, evidence, and applications remain until they are individually deleted.</text>
    </view>
  </scroll-view>
</template>

<style scoped>
.page { min-height: 100vh; box-sizing: border-box; padding: 28rpx; background: #f7f8fa; color: #1f2329; }.title,.section-title,.description { display: block; }.title { font-size: 40rpx; font-weight: 700; }.section { margin-top: 22rpx; padding: 24rpx; background: #fff; border: 1rpx solid #e5e6eb; border-radius: 12rpx; }.section-title { font-size: 30rpx; font-weight: 600; }.description { margin-top: 14rpx; color: #4e5969; font-size: 25rpx; line-height: 1.6; }.danger { margin-top: 22rpx; color: #d4380d; background: #fff1f0; border: 1rpx solid #ffccc7; }
</style>
