<script setup lang="ts">
import { computed } from "vue"

import ResumePreview from "../../components/ResumePreview.vue"
import { requestPdfExport, requestWordExport } from "../../services/export-api"
import { saveDraft } from "../../services/resume-api"
import { useResumeStore } from "../../stores/resume"
import { getClientId } from "../../stores/session"
import { validateResume } from "../../utils/validators"
import { downloadExport } from "../../utils/download-export"

const store = useResumeStore()
const resume = computed(() => store.draft.resume)

function backToForm() {
  uni.navigateTo({ url: "/pages/resume-form/index" })
}

function openApplicationTracker() {
  const params = new URLSearchParams()
  if (resume.value.job.targetRole) params.set("roleName", resume.value.job.targetRole)
  if (resume.value.basic.city) params.set("city", resume.value.basic.city)
  if (store.draft.id) params.set("draftId", store.draft.id)
  uni.navigateTo({ url: `/pages/applications/index?${params}` })
}

async function save(): Promise<boolean> {
  const errors = validateResume(resume.value)
  if (errors.length) {
    uni.showToast({ title: errors[0].message, icon: "none" })
    return false
  }
  try {
    const saved = await saveDraft(getClientId(), store.draft)
    store.draft.id = saved.id
    store.checkpoint()
    uni.showToast({ title: "草稿已保存", icon: "success" })
    return true
  } catch {
    store.checkpoint()
    uni.showToast({ title: "网络异常，已保留本地草稿", icon: "none" })
  }
  return false
}

async function exportResume(kind: "word" | "pdf") {
  if (!store.draft.id && !(await save())) return
  if (!store.draft.id) return
  try {
    const result = kind === "word"
      ? await requestWordExport(getClientId(), store.draft.id)
      : await requestPdfExport(getClientId(), store.draft.id)
    await downloadExport(
      result.downloadUrl,
      result.filename,
      process.env.UNI_PLATFORM === "mp-weixin" ? "mp-weixin" : "h5",
    )
  } catch (reason) {
    uni.showToast({ title: reason instanceof Error ? reason.message : "导出失败，请稍后重试", icon: "none" })
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
        <button size="mini" @click="openApplicationTracker">加入投递计划</button>
        <button size="mini" class="primary" @click="save">保存草稿</button>
        <button size="mini" @click="exportResume('word')">导出 Word</button>
        <button size="mini" @click="exportResume('pdf')">导出 PDF</button>
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
