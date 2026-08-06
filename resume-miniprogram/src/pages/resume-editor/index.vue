<script setup lang="ts">
import { computed } from "vue"

import ResumePreview from "../../components/ResumePreview.vue"
import { saveDraft } from "../../services/resume-api"
import { useResumeStore } from "../../stores/resume"
import { getClientId } from "../../stores/session"
import { validateResume } from "../../utils/validators"

const store = useResumeStore()
const resume = computed(() => store.draft.resume)

function backToForm() {
  uni.navigateTo({ url: "/pages/resume-form/index" })
}

async function save() {
  const errors = validateResume(resume.value)
  if (errors.length) {
    uni.showToast({ title: errors[0].message, icon: "none" })
    return
  }
  try {
    const saved = await saveDraft(getClientId(), store.draft)
    store.draft.id = saved.id
    store.checkpoint()
    uni.showToast({ title: "草稿已保存", icon: "success" })
  } catch {
    store.checkpoint()
    uni.showToast({ title: "网络异常，已保留本地草稿", icon: "none" })
  }
}
</script>

<template>
  <scroll-view class="page" scroll-y>
    <view class="toolbar">
      <view>
        <text class="title">简历预览</text>
        <text class="subtitle">当前模板：{{ store.draft.templateId }}</text>
      </view>
      <view class="toolbar-actions">
        <button size="mini" @click="backToForm">返回填写</button>
        <button size="mini" class="primary" @click="save">保存草稿</button>
      </view>
    </view>
    <ResumePreview :resume="resume" :template-id="store.draft.templateId" />
  </scroll-view>
</template>

<style scoped>
.page { height: 100vh; padding: 28rpx; box-sizing: border-box; background: #f7f8fa; }
.toolbar { display: flex; justify-content: space-between; gap: 24rpx; align-items: center; margin-bottom: 24rpx; }.title { display: block; color: #1f2329; font-size: 40rpx; font-weight: 700; }.subtitle { display: block; margin-top: 8rpx; color: #86909c; font-size: 23rpx; }
.toolbar-actions { display: flex; gap: 12rpx; }.primary { color: #fff; background: #1677ff; }
</style>
