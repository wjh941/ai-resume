<script setup lang="ts">
import { ref } from "vue"
import { queryJob } from "../../services/resume-api"
import { useResumeStore } from "../../stores/resume"

const roleName = ref("")
const loading = ref(false)
const error = ref("")
const store = useResumeStore()

async function search() {
  const role = roleName.value.trim()
  if (!role) {
    error.value = "请输入岗位名称"
    return
  }
  loading.value = true
  error.value = ""
  try {
    store.setJobIntelligence(await queryJob(role))
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : "岗位查询失败"
  } finally {
    loading.value = false
  }
}

function startResume() {
  if (!store.activeJob) return
  uni.navigateTo({ url: "/pages/resume-form/index" })
}
</script>

<template>
  <view class="page">
    <view class="hero"><text class="title">AI 岗位情报</text><text class="subtitle">先了解目标岗位，再生成匹配简历</text></view>
    <view class="search-card">
      <input v-model="roleName" placeholder="例如：数据工程师" confirm-type="search" @confirm="search" />
      <button class="primary" :loading="loading" @click="search">查询岗位情报</button>
      <text v-if="error" class="error">{{ error }}</text>
    </view>
    <view v-if="store.activeJob" class="result">
      <text class="role">{{ store.activeJob.roleName }}</text>
      <view class="block"><text>薪资区间</text><text v-for="(value, key) in store.activeJob.salaryByExperience" :key="key">{{ key }}：{{ value }}</text></view>
      <view class="block"><text>工作职责</text><text v-for="item in store.activeJob.responsibilities" :key="item">• {{ item }}</text></view>
      <view class="block"><text>必备技能</text><text>{{ store.activeJob.requiredSkills.join(" / ") }}</text></view>
      <view class="block"><text>发展路线</text><text>{{ store.activeJob.careerRoute.join(" → ") }}</text></view>
      <button class="primary" @click="startResume">以此岗位生成简历</button>
    </view>
  </view>
</template>

<style scoped>
.page { padding: 32rpx; }
.hero { padding: 24rpx 0 32rpx; }.title { display: block; font-size: 44rpx; font-weight: 700; }.subtitle { color: #86909c; font-size: 26rpx; }
.search-card,.result { padding: 24rpx; background: #fff; border-radius: 18rpx; box-shadow: 0 8rpx 24rpx rgba(31,35,41,.06); }
input { height: 80rpx; margin-bottom: 18rpx; padding: 0 20rpx; background: #f7f8fa; border-radius: 12rpx; }.primary { color: #fff; background: #1677ff; }
.result { margin-top: 24rpx; }.role { display: block; font-size: 36rpx; font-weight: 700; }.block { display: flex; flex-direction: column; gap: 8rpx; margin: 24rpx 0; color: #4e5969; }.block > text:first-child { color: #1f2329; font-weight: 600; }.error { display: block; margin-top: 12rpx; color: #d03050; }
</style>
