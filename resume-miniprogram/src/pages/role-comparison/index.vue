<script setup lang="ts">
import { onMounted, ref } from "vue"

import { compareRoles } from "../../services/career-api"
import { useCareerStore } from "../../stores/career"
import { getClientId } from "../../stores/session"
import type { CareerComparisonResult, CareerComparisonItem } from "../../types/career"
import { canOpenComparison } from "../../utils/role-comparison"

const careerStore = useCareerStore()
const result = ref<CareerComparisonResult | null>(null)
const loading = ref(false)
const error = ref("")

async function loadComparison() {
  if (!canOpenComparison(careerStore.comparisonRoleNames)) {
    error.value = "请返回规划页选择 2-4 个岗位后再进行对比。"
    return
  }
  loading.value = true
  error.value = ""
  try {
    result.value = await compareRoles(getClientId(), careerStore.comparisonRoleNames)
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : "岗位对比加载失败，请检查后端服务。"
  } finally {
    loading.value = false
  }
}

function setWeeklyTarget(item: CareerComparisonItem) {
  careerStore.setWeeklyTarget(item)
  uni.showToast({ title: `已设为本周主目标：${item.role.roleName}`, icon: "success" })
}

onMounted(() => {
  void loadComparison()
})
</script>

<template>
  <scroll-view class="page" scroll-y>
    <view class="content">
      <view class="hero">
        <text class="eyebrow">LOCAL ROLE COMPARISON</text>
        <text class="title">岗位横向对比</text>
        <text class="subtitle">依据本地岗位库、你的职业画像和已确认经历比较方向；分数不是录用概率。</text>
      </view>

      <view v-if="careerStore.weeklyTarget" class="target-card">
        <text>本周主目标</text>
        <text>{{ careerStore.weeklyTarget.roleName }} · {{ careerStore.weeklyTarget.totalScore }}/100</text>
      </view>
      <view v-if="error" class="error-card">{{ error }}</view>
      <view v-else-if="loading" class="loading">正在生成本地岗位对比…</view>

      <template v-else-if="result">
        <view v-if="result.commonStrengths.length" class="common-card">
          <text class="section-title">共有优势</text>
          <text v-for="item in result.commonStrengths" :key="item" class="bullet">- {{ item }}</text>
        </view>
        <view v-for="item in result.items" :key="item.role.roleName" class="role-card">
          <view class="role-top">
            <view>
              <text class="role-name">{{ item.role.roleName }}</text>
              <text class="role-family">{{ item.role.family }}</text>
            </view>
            <view class="score"><text>{{ item.totalScore }}</text><text>/100</text></view>
          </view>
          <text class="description">{{ item.role.description }}</text>
          <view class="chip-row"><text v-for="advantage in item.matchingAdvantages" :key="advantage" class="chip positive">{{ advantage }}</text></view>
          <text v-if="item.missingSkills.length" class="gap">待补齐：{{ item.missingSkills.join("、") }}</text>
          <view class="score-list"><text v-for="score in item.scoreBreakdown" :key="score.key">{{ score.label }} {{ score.score }}/{{ score.maxScore }} · {{ score.reason }}</text></view>
          <view class="risk">{{ item.riskNotice }}</view>

          <view class="plan-section"><text>7 天行动</text><text v-for="task in item.actionPlan.sevenDay" :key="task">- {{ task }}</text></view>
          <view class="plan-section"><text>30 天行动</text><text v-for="task in item.actionPlan.thirtyDay" :key="task">- {{ task }}</text></view>
          <view class="plan-section"><text>90 天行动</text><text v-for="task in item.actionPlan.ninetyDay" :key="task">- {{ task }}</text></view>
          <button class="primary" @click="setWeeklyTarget(item)">设为本周主目标</button>
        </view>
        <text class="notice">{{ result.recommendationNotice }}</text>
      </template>
    </view>
  </scroll-view>
</template>

<style scoped>
.page { min-height: 100vh; background: #f4f7fb; color: #1f2937; }.content { padding: 24rpx 24rpx 52rpx; }
.hero,.role-card,.common-card,.target-card { padding: 24rpx; background: #fff; border: 1rpx solid #e3edf8; border-radius: 20rpx; box-shadow: 0 8rpx 24rpx rgba(35,78,130,.06); }
.hero { background: linear-gradient(145deg,#e7f1ff,#f9fcff); }.eyebrow { display: block; color: #1677ff; font-size: 21rpx; font-weight: 700; letter-spacing: 1rpx; }.title { display: block; margin-top: 10rpx; font-size: 44rpx; font-weight: 700; }.subtitle { display: block; margin-top: 12rpx; color: #64748b; font-size: 25rpx; line-height: 1.6; }
.target-card,.common-card,.role-card,.error-card,.loading { margin-top: 20rpx; }.target-card { display: flex; justify-content: space-between; gap: 16rpx; color: #245b99; background: #eef8ff; border-color: #c7e5ff; font-size: 26rpx; font-weight: 700; }.error-card,.loading { padding: 28rpx; color: #8f341e; background: #fff7f0; border: 1rpx solid #ffd8bf; border-radius: 16rpx; line-height: 1.55; }.loading { color: #59728d; background: #fff; border-color: #e3edf8; }
.section-title { display: block; color: #245b99; font-size: 30rpx; font-weight: 700; }.bullet { display: block; margin-top: 12rpx; color: #4e5969; font-size: 24rpx; line-height: 1.5; }
.role-top { display: flex; justify-content: space-between; align-items: center; gap: 16rpx; }.role-name { display: block; font-size: 34rpx; font-weight: 700; }.role-family { display: block; margin-top: 7rpx; color: #86909c; font-size: 22rpx; }.score { min-width: 90rpx; height: 90rpx; display: flex; flex-direction: column; justify-content: center; align-items: center; color: #1677ff; background: #e8f3ff; border-radius: 50%; }.score text:first-child { font-size: 32rpx; font-weight: 700; }.score text:last-child { font-size: 19rpx; }
.description,.notice { display: block; margin-top: 16rpx; color: #64748b; font-size: 24rpx; line-height: 1.6; }.chip-row { display: flex; flex-wrap: wrap; gap: 10rpx; margin-top: 16rpx; }.chip { padding: 7rpx 12rpx; border-radius: 999rpx; font-size: 22rpx; }.positive { color: #1677ff; background: #e8f3ff; }.gap { display: block; margin-top: 14rpx; color: #c2410c; font-size: 24rpx; }
.score-list { padding: 12rpx 0; }.score-list text,.plan-section text { display: block; margin-top: 8rpx; color: #5f6f82; font-size: 22rpx; line-height: 1.5; }.risk { margin-top: 12rpx; padding: 14rpx; color: #8a5a00; background: #fffbe8; border-radius: 12rpx; font-size: 22rpx; line-height: 1.5; }.plan-section { margin-top: 16rpx; padding: 16rpx; background: #f8fafc; border-radius: 12rpx; }.plan-section text:first-child { margin-top: 0; color: #245b99; font-size: 25rpx; font-weight: 700; }
button { margin-top: 20rpx; border-radius: 12rpx; font-size: 26rpx; }.primary { color: #fff; background: #1677ff; }.notice { padding: 4rpx 6rpx; font-size: 21rpx; }
</style>
