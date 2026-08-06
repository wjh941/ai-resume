<script setup lang="ts">
import { computed, ref } from "vue"

import { queryJobConsultation, reviewResumeText } from "../../services/resume-api"
import { IDENTITY_OPTIONS, IDENTITY_PROMPT, useConsultationStore } from "../../stores/consultation"
import { useResumeStore } from "../../stores/resume"
import type { JobConsultation, ResumeReview } from "../../types/consultation"
import { prepareResumeForJob } from "../../utils/resume-autofill"

const roleName = ref("")
const resumeText = ref("")
const loading = ref(false)
const reviewLoading = ref(false)
const error = ref("")
const reviewError = ref("")
const jobConsultation = ref<JobConsultation | null>(null)
const resumeReview = ref<ResumeReview | null>(null)
const store = useResumeStore()
const consultation = useConsultationStore()
const identityPromptLines = IDENTITY_PROMPT.split("\n")
const canReviewResume = computed(() => consultation.identityCode !== null)

function beginIdentitySelection() {
  const role = roleName.value.trim()
  if (!role) {
    error.value = "请输入岗位名称"
    return
  }
  error.value = ""
  reviewError.value = ""
  jobConsultation.value = null
  resumeReview.value = null
  consultation.beginIdentitySelection(role)
}

async function selectIdentity(identityCode: (typeof IDENTITY_OPTIONS)[number]["code"]) {
  consultation.selectIdentity(identityCode)
  loading.value = true
  error.value = ""
  try {
    const result = await queryJobConsultation(consultation.pendingRoleName, identityCode)
    jobConsultation.value = result
    store.setJobIntelligence(result.jobIntelligence)
    consultation.showJobAnalysis()
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : "岗位解析失败"
  } finally {
    loading.value = false
  }
}

function startResume() {
  if (!jobConsultation.value) return
  prepareResumeForJob(store.draft, jobConsultation.value.jobIntelligence)
  store.checkpoint()
  uni.navigateTo({ url: "/pages/template-picker/index" })
}

async function reviewResume() {
  const text = resumeText.value.trim()
  if (!text) {
    reviewError.value = "请粘贴需要优化的简历内容"
    return
  }
  if (!consultation.identityCode) {
    reviewError.value = "请先选择求职身份"
    return
  }
  reviewLoading.value = true
  reviewError.value = ""
  resumeReview.value = null
  try {
    resumeReview.value = await reviewResumeText(
      text,
      consultation.identityCode,
      jobConsultation.value?.jobIntelligence.roleName || consultation.pendingRoleName,
    )
  } catch (reason) {
    reviewError.value = reason instanceof Error ? reason.message : "简历优化失败"
  } finally {
    reviewLoading.value = false
  }
}
</script>

<template>
  <view class="page">
    <view class="hero">
      <text class="title">AI 岗位情报</text>
      <text class="subtitle">先选择求职身份，再获得岗位解析与对应求职方案</text>
    </view>

    <view class="search-card">
      <input v-model="roleName" placeholder="例如：数据工程师" confirm-type="search" @confirm="beginIdentitySelection" />
      <button class="primary" @click="beginIdentitySelection">查询岗位情报</button>
      <text v-if="error" class="error">{{ error }}</text>
    </view>

    <view v-if="consultation.stage === 'identity-selection'" class="identity-card">
      <text v-for="line in identityPromptLines" :key="line" class="identity-prompt">{{ line }}</text>
      <view class="identity-options">
        <button
          v-for="option in IDENTITY_OPTIONS"
          :key="option.code"
          class="identity-button"
          :loading="loading"
          @click="selectIdentity(option.code)"
        >
          {{ option.code }} - {{ option.label }}
        </button>
      </view>
    </view>

    <view v-if="jobConsultation" class="result">
      <text class="role">{{ jobConsultation.jobIntelligence.roleName }}</text>
      <text class="result-title">## 岗位全维度解析</text>
      <view v-for="section in jobConsultation.jobAnalysisSections" :key="section.order" class="block">
        <text class="block-title">## {{ section.order }}. {{ section.title }}</text>
        <text v-for="item in section.items" :key="item" class="list-item">- {{ item }}</text>
      </view>

      <text class="result-title">## 对应人群专属简历&求职实操方案</text>
      <text class="identity-name">{{ jobConsultation.identityPlan.title }}</text>
      <view v-for="section in jobConsultation.identityPlan.sections" :key="section.order" class="block plan-block">
        <text class="block-title">## {{ section.title }}</text>
        <text v-for="item in section.items" :key="item" class="list-item">- {{ item }}</text>
      </view>
      <text class="follow-up">{{ jobConsultation.followUpQuestion }}</text>
      <button class="primary" @click="startResume">以此岗位生成简历</button>
    </view>

    <view v-if="canReviewResume" class="review-card">
      <text class="review-title">粘贴简历，获得针对性优化</text>
      <textarea
        v-model="resumeText"
        class="resume-textarea"
        placeholder="直接粘贴简历文本。系统将根据已选择的求职身份给出修改点和替换范文。"
        auto-height
      />
      <button class="primary" :loading="reviewLoading" @click="reviewResume">优化这份简历</button>
      <text v-if="reviewError" class="error">{{ reviewError }}</text>
    </view>

    <view v-if="resumeReview" class="result review-result">
      <text class="result-title">## 简历问题逐条标注</text>
      <text v-for="item in resumeReview.issues" :key="item" class="list-item">- {{ item }}</text>
      <text class="result-title">## 逐段优化范文</text>
      <text v-for="item in resumeReview.rewriteExamples" :key="item" class="list-item">- {{ item }}</text>
      <text class="result-title">## 加分关键词</text>
      <text class="keywords">{{ resumeReview.keywords.join(" / ") }}</text>
    </view>
  </view>
</template>

<style scoped>
.page { padding: 32rpx; background: #f7f8fa; }
.hero { padding: 24rpx 0 32rpx; }
.title { display: block; font-size: 44rpx; font-weight: 700; color: #1f2329; }
.subtitle { display: block; margin-top: 10rpx; color: #86909c; font-size: 26rpx; }
.search-card,.result,.identity-card,.review-card {
  margin-top: 24rpx; padding: 24rpx; background: #fff; border: 1rpx solid #e5e6eb;
  border-radius: 18rpx; box-shadow: 0 8rpx 24rpx rgba(31,35,41,.06);
}
input,.resume-textarea {
  width: 100%; box-sizing: border-box; padding: 20rpx; background: #f7f8fa; border-radius: 12rpx;
}
input { height: 80rpx; margin-bottom: 18rpx; }
.resume-textarea { min-height: 180rpx; margin: 20rpx 0; line-height: 1.6; }
.primary { margin-top: 12rpx; color: #fff; background: #1677ff; }
.identity-prompt { display: block; margin-bottom: 12rpx; font-weight: 600; color: #1f2329; }
.identity-options { display: flex; flex-direction: column; gap: 14rpx; margin-top: 24rpx; }
.identity-button { margin: 0; text-align: left; color: #1677ff; background: #e8f3ff; border: 1rpx solid #b7d8ff; }
.role,.result-title,.review-title { display: block; font-weight: 700; color: #1f2329; }
.role { font-size: 36rpx; }.result-title { margin-top: 32rpx; font-size: 32rpx; }
.review-title { font-size: 32rpx; }
.identity-name { display: block; margin-top: 18rpx; color: #1677ff; font-weight: 600; }
.block { display: flex; flex-direction: column; gap: 10rpx; margin: 24rpx 0; color: #4e5969; }
.block-title { color: #1f2329; font-weight: 600; }.list-item { line-height: 1.65; }
.plan-block { padding: 20rpx; background: #f7faff; border-radius: 12rpx; }
.follow-up,.keywords { display: block; margin: 20rpx 0; color: #4e5969; line-height: 1.6; }
.review-result { margin-top: 24rpx; }.error { display: block; margin-top: 12rpx; color: #d03050; }
</style>
