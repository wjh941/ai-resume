<script setup lang="ts">
import { ref } from "vue"

import { useCareerStore } from "../../stores/career"
import { useConsultationStore } from "../../stores/consultation"
import { useApplicationsStore } from "../../stores/applications"
import { useResumeStore } from "../../stores/resume"
import { clearLocalCareerWorkspace } from "../../utils/local-privacy"
import { exportLocalBackupFile, importLocalBackupFile } from "../../utils/local-backup-file"
import { parseLocalBackup, serializeLocalBackup } from "../../utils/local-backup"
import { toUserMessage } from "../../services/http"
import { showErrorToast } from "../../utils/error-feedback"

const resumeStore = useResumeStore()
const careerStore = useCareerStore()
const consultationStore = useConsultationStore()
const applicationsStore = useApplicationsStore()
const backupBusy = ref(false)

async function exportBackup(): Promise<void> {
  backupBusy.value = true
  try {
    await exportLocalBackupFile(serializeLocalBackup(resumeStore.exportBackup(), careerStore.exportBackup()))
    uni.showToast({ title: "备份文件已生成", icon: "success" })
  } catch (reason) {
    showErrorToast(toUserMessage(reason, "备份文件创建失败，请稍后重试。"))
  } finally {
    backupBusy.value = false
  }
}

async function restoreBackup(): Promise<void> {
  backupBusy.value = true
  try {
    const backup = parseLocalBackup(await importLocalBackupFile())
    if (!resumeStore.restoreBackup(backup.resume) || !careerStore.restoreBackup(backup.career)) {
      throw new Error("备份文件无效或格式不受支持。")
    }
    uni.showToast({ title: "本机备份已恢复", icon: "success" })
  } catch (reason) {
    showErrorToast(toUserMessage(reason, "备份文件恢复失败，请稍后重试。"))
  } finally {
    backupBusy.value = false
  }
}

function confirmRestoreBackup(): void {
  uni.showModal({
    title: "恢复本机备份",
    content: "将使用备份替换本机上的简历与职业规划数据；服务端记录不会变化。确定继续吗？",
    success: (result) => {
      if (result.confirm) void restoreBackup()
    },
  })
}

function clearLocalData(): void {
  uni.showModal({
    title: "清理本机工作区",
    content: "将清除本机上的草稿检查点、职业规划与待同步投递记录；服务端数据不受影响。确定继续吗？",
    success: (result) => {
      if (!result.confirm) return
      clearLocalCareerWorkspace()
      resumeStore.resetDraft(false)
      careerStore.resetPlanner(false)
      consultationStore.resetConsultation(false)
      applicationsStore.clearLocalData()
      uni.showToast({ title: "本机工作区已清理", icon: "success" })
    },
  })
}
</script>

<template>
  <scroll-view class="page" scroll-y>
    <text class="title">本地隐私</text>
    <view class="section">
      <text class="section-title">备份本机数据</text>
      <text class="description">将本机简历草稿和职业规划工作区导出或恢复为 JSON 文件，不包含服务端记录。</text>
      <view class="backup-actions">
        <button :loading="backupBusy" :disabled="backupBusy" @click="exportBackup">导出本地备份</button>
        <button :loading="backupBusy" :disabled="backupBusy" class="secondary" @click="confirmRestoreBackup">恢复本地备份</button>
      </view>
    </view>
    <view class="section">
      <text class="section-title">清理本机数据</text>
      <text class="description">删除本地简历、职业规划、咨询、测评状态和待同步投递记录。</text>
      <button class="danger" @click="clearLocalData">清理本地工作区</button>
    </view>
    <view class="section">
      <text class="section-title">服务端记录</text>
      <text class="description">服务端草稿、经历证据和投递记录需要单独删除，清理本机数据不会影响它们。</text>
    </view>
  </scroll-view>
</template>

<style scoped>
.page { min-height: 100vh; box-sizing: border-box; padding: 28rpx; background: #f7f8fa; color: #1f2329; }.title,.section-title,.description { display: block; }.title { font-size: 40rpx; font-weight: 700; }.section { margin-top: 22rpx; padding: 24rpx; background: #fff; border: 1rpx solid #e5e6eb; border-radius: 12rpx; }.section-title { font-size: 30rpx; font-weight: 600; }.description { margin-top: 14rpx; color: #4e5969; font-size: 25rpx; line-height: 1.6; }.backup-actions { display: flex; gap: 14rpx; margin-top: 22rpx; }.backup-actions button { flex: 1; margin: 0; font-size: 24rpx; }.secondary { color: #1677ff; background: #eef6ff; border: 1rpx solid #b7d8ff; }.danger { margin-top: 22rpx; color: #d4380d; background: #fff1f0; border: 1rpx solid #ffccc7; }
</style>
