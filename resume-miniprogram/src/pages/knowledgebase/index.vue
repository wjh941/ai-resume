<script setup lang="ts">
import { onMounted, ref } from "vue"

import { listKnowledgeSources, startOfficialKnowledgeSync } from "../../services/knowledge-sync-api"
import type { KnowledgeSource, KnowledgeSyncSummary } from "../../types/knowledge-sync"

const sources = ref<KnowledgeSource[]>([])
const lastRun = ref<KnowledgeSyncSummary | null>(null)
const loading = ref(false)
const error = ref("")

async function loadSources() {
  try {
    sources.value = await listKnowledgeSources()
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : "无法读取知识库数据源状态"
  }
}

async function initializeKnowledgebase() {
  error.value = ""
  loading.value = true
  try {
    lastRun.value = await startOfficialKnowledgeSync()
    await loadSources()
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : "岗位库初始化失败"
  } finally {
    loading.value = false
  }
}

onMounted(loadSources)
</script>

<template>
  <scroll-view class="page" scroll-y>
    <view class="content">
      <view class="hero">
        <text class="eyebrow">COMPLIANT KNOWLEDGEBASE</text>
        <text class="title">岗位知识库</text>
        <text class="subtitle">仅同步已核验的官方静态 CSV/JSON 数据集；不抓取招聘网站，不采集职位描述。</text>
      </view>

      <view class="card action-card">
        <view>
          <text class="section-title">初始化完整岗位库</text>
          <text class="hint">自动下载、解析并增量写入已启用的合规官方数据源，用户手动维护的岗位不会被覆盖。</text>
        </view>
        <button class="primary" :loading="loading" @click="initializeKnowledgebase">一键初始化完整岗位库</button>
        <text v-if="error" class="error">{{ error }}</text>
      </view>

      <view v-if="lastRun" class="card summary">
        <text class="section-title">本次同步结果</text>
        <view class="stats">
          <view><text>{{ lastRun.addedRoles }}</text><text>新增岗位</text></view>
          <view><text>{{ lastRun.addedMajors }}</text><text>新增专业</text></view>
          <view><text>{{ lastRun.skippedRows }}</text><text>跳过记录</text></view>
        </view>
        <text v-for="item in lastRun.errors" :key="item" class="error">{{ item }}</text>
      </view>

      <view class="card">
        <view class="section-heading">
          <text class="section-title">数据源状态</text>
          <text class="hint">仅支持 HTTPS 直链及 CSV、JSON、ZIP 内 CSV/JSON</text>
        </view>
        <view v-for="source in sources" :key="source.sourceKey" class="source-row">
          <view>
            <text class="source-name">{{ source.displayName }}</text>
            <text class="source-detail">{{ source.parserKind }} · {{ source.fileFormat.toUpperCase() }} · {{ source.allowedHosts.join(", ") }}</text>
            <text v-if="source.disabledReason" class="disabled-reason">{{ source.disabledReason }}</text>
          </view>
          <text class="badge" :class="{ enabled: source.enabled }">{{ source.enabled ? "已启用" : "待核验" }}</text>
        </view>
      </view>
    </view>
  </scroll-view>
</template>

<style scoped>
.page { min-height: 100vh; background: #f4f7fb; color: #1f2937; }
.content { padding: 24rpx 24rpx 54rpx; }
.hero { padding: 34rpx 26rpx; background: linear-gradient(145deg, #e8f3ff, #f8fbff); border-radius: 24rpx; }
.eyebrow { display: block; color: #1677ff; font-size: 21rpx; font-weight: 700; letter-spacing: 1rpx; }
.title { display: block; margin-top: 10rpx; font-size: 44rpx; font-weight: 700; }
.subtitle, .hint, .source-detail, .disabled-reason { display: block; color: #6b7280; font-size: 24rpx; line-height: 1.6; }
.subtitle { margin-top: 12rpx; }
.card { margin-top: 20rpx; padding: 24rpx; background: #fff; border: 1rpx solid #e5edf6; border-radius: 20rpx; box-shadow: 0 8rpx 24rpx rgba(35, 78, 130, .06); }
.section-heading { display: flex; justify-content: space-between; gap: 16rpx; }
.section-title { display: block; font-size: 30rpx; font-weight: 700; }
.action-card .hint { margin-top: 10rpx; }
.primary { margin-top: 20rpx; border-radius: 14rpx; background: #1677ff; color: #fff; font-size: 27rpx; }
.stats { display: flex; gap: 16rpx; margin-top: 20rpx; }
.stats view { flex: 1; padding: 18rpx 12rpx; background: #f4f8fd; border-radius: 14rpx; text-align: center; }
.stats text:first-child { display: block; color: #1677ff; font-size: 38rpx; font-weight: 700; }
.stats text:last-child { color: #6b7280; font-size: 22rpx; }
.source-row { display: flex; justify-content: space-between; gap: 18rpx; padding: 22rpx 0; border-bottom: 1rpx solid #edf1f5; }
.source-row:last-child { border-bottom: 0; }
.source-name { display: block; font-size: 28rpx; font-weight: 600; }
.source-detail { margin-top: 6rpx; }
.disabled-reason { margin-top: 6rpx; color: #b7791f; }
.badge { align-self: flex-start; padding: 6rpx 14rpx; border-radius: 999rpx; background: #fff7e6; color: #b7791f; font-size: 22rpx; }
.badge.enabled { background: #e8f7ef; color: #16794b; }
.error { display: block; margin-top: 14rpx; color: #d4380d; font-size: 24rpx; }
</style>
