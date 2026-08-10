<script setup lang="ts">
import { computed, ref, watch } from "vue"

import {
  generateCareerRecommendations,
  loadCareerProfile,
  queryMajorSuggestions,
  saveCareerProfile,
} from "../../services/career-api"
import { queryJob } from "../../services/resume-api"
import { useCareerStore } from "../../stores/career"
import { useResumeStore } from "../../stores/resume"
import { getClientId } from "../../stores/session"
import type { CareerIdentityCode, CareerProfilePayload, MajorSuggestion, RecommendationTier, RoleRecommendation } from "../../types/career"
import { prepareResumeForJob } from "../../utils/resume-autofill"

const store = useCareerStore()
const resumeStore = useResumeStore()

const identityOptions: Array<{ code: CareerIdentityCode; label: string }> = [
  { code: "1", label: "在校学生 / 实习" },
  { code: "2", label: "应届毕业生 / 校招" },
  { code: "3", label: "在职跳槽" },
  { code: "4", label: "待业求职" },
  { code: "5", label: "零基础转行" },
]
const tierOptions: Array<{ key: RecommendationTier; label: string; hint: string }> = [
  { key: "stretch", label: "冲刺", hint: "方向有潜力，但需要补齐关键能力" },
  { key: "stable", label: "稳妥", hint: "专业、技能和偏好匹配度较高" },
  { key: "safe", label: "保底", hint: "门槛相对友好，可作为过渡方向" },
]

const profile = ref<CareerProfilePayload>(store.profile ?? {
  clientId: getClientId(),
  identityCode: "2",
  major: "",
  educationLevel: "本科",
  graduationYear: null,
  cityPreferences: [],
  minimumSalary: "",
  industryPreferences: [],
  workTypes: ["全职"],
  skills: [],
  draftId: null,
})
const majorQuery = ref(profile.value.major)
const majorSuggestions = ref<MajorSuggestion[]>([])
const citiesText = ref(profile.value.cityPreferences.join("、"))
const industriesText = ref(profile.value.industryPreferences.join("、"))
const skillsText = ref(profile.value.skills.join("、"))
const loading = ref(false)
const resumeLoading = ref("")
const error = ref("")

const selectedTier = computed({
  get: () => store.selectedTier,
  set: (value: RecommendationTier) => { store.selectedTier = value; store.checkpoint() },
})
const recommendations = computed(() => store.result?.tiers[selectedTier.value] ?? [])
const majorReport = computed(() => store.result?.majorReport ?? null)

watch(majorQuery, async (value) => {
  const query = value.trim()
  if (!query) {
    majorSuggestions.value = []
    return
  }
  try {
    majorSuggestions.value = await queryMajorSuggestions(query)
  } catch {
    majorSuggestions.value = []
  }
})

function splitValues(value: string): string[] {
  return value.split(/[、,，\n]/).map((item) => item.trim()).filter(Boolean)
}

function selectIdentity(event: Event) {
  const index = Number((event as unknown as { detail?: { value?: string } }).detail?.value)
  if (identityOptions[index]) profile.value.identityCode = identityOptions[index].code
}

function selectMajor(item: MajorSuggestion) {
  profile.value.major = item.majorName
  majorQuery.value = item.majorName
  majorSuggestions.value = []
}

function buildPayload(): CareerProfilePayload {
  return {
    ...profile.value,
    clientId: getClientId(),
    major: majorQuery.value.trim(),
    cityPreferences: splitValues(citiesText.value),
    industryPreferences: splitValues(industriesText.value),
    skills: splitValues(skillsText.value),
  }
}

function openCareerAssessment() {
  uni.navigateTo({ url: '/pages/career-assessment/index' })
}

async function generatePlan() {
  const payload = buildPayload()
  if (!payload.major) {
    error.value = "请先填写专业，可填写跨专业目标。"
    return
  }
  error.value = ""
  loading.value = true
  try {
    const saved = await saveCareerProfile(payload)
    const result = await generateCareerRecommendations(saved.clientId)
    store.setResult(result)
    selectedTier.value = "stable"
    uni.pageScrollTo({ scrollTop: 620, duration: 250 })
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : "规划生成失败，请检查后端服务。"
  } finally {
    loading.value = false
  }
}

async function loadSavedProfile() {
  try {
    const saved = await loadCareerProfile(getClientId())
    profile.value = {
      clientId: saved.clientId, identityCode: saved.identityCode, major: saved.major,
      educationLevel: saved.educationLevel, graduationYear: saved.graduationYear,
      cityPreferences: saved.cityPreferences, minimumSalary: saved.minimumSalary,
      industryPreferences: saved.industryPreferences, workTypes: saved.workTypes,
      skills: saved.skills, draftId: saved.draftId,
    }
    majorQuery.value = saved.major
    citiesText.value = saved.cityPreferences.join("、")
    industriesText.value = saved.industryPreferences.join("、")
    skillsText.value = saved.skills.join("、")
  } catch {
    // A new anonymous device may not have saved a profile yet.
  }
}

async function useForResume(recommendation: RoleRecommendation) {
  resumeLoading.value = recommendation.role.roleName
  try {
    const job = await queryJob(recommendation.role.roleName)
    resumeStore.setJobIntelligence(job)
    prepareResumeForJob(resumeStore.draft, job)
    resumeStore.checkpoint()
    store.selectRole(recommendation)
    uni.navigateTo({ url: "/pages/template-picker/index" })
  } catch (reason) {
    uni.showToast({ title: reason instanceof Error ? reason.message : "岗位载入失败", icon: "none" })
  } finally {
    resumeLoading.value = ""
  }
}

store.restoreCheckpoint()
void loadSavedProfile()
</script>

<template>
  <scroll-view class="page" scroll-y>
    <view class="content">
      <view class="hero">
        <text class="eyebrow">CAREER VOLUNTEER PLANNER</text>
        <text class="title">求职志愿规划</text>
        <text class="subtitle">用专业、技能和偏好比较冲刺、稳妥、保底方向，不承诺录用结果。</text>
      </view>

      <view class="assessment-brief">
        <view>
          <text class="assessment-brief-title">职业测评与年度洞察</text>
          <text class="assessment-brief-text">先整理兴趣、真实证据与现实约束，再结合专业生成更可执行的方向建议。</text>
        </view>
        <button class="assessment-entry" @click="openCareerAssessment">开始测评</button>
      </view>
      <view class="card profile-card">
        <view class="section-heading">
          <text>建立求职画像</text>
          <text class="hint">信息越完整，推荐越具体</text>
        </view>
        <view class="field">
          <text>求职身份</text>
          <picker :range="identityOptions.map((item) => item.label)" @change="selectIdentity">
            <view class="picker">{{ identityOptions.find((item) => item.code === profile.identityCode)?.label }}</view>
          </picker>
        </view>
        <view class="field">
          <text>所学专业</text>
          <input v-model="majorQuery" placeholder="例如：计算机科学与技术，或填写跨专业方向" />
          <view v-if="majorSuggestions.length" class="suggestions">
            <view v-for="item in majorSuggestions" :key="item.majorName" class="suggestion" @click="selectMajor(item)">
              <text>{{ item.majorName }}</text><text>{{ item.category }}</text>
            </view>
          </view>
        </view>
        <view class="two-columns">
          <view class="field">
            <text>学历</text>
            <input v-model="profile.educationLevel" placeholder="本科" />
          </view>
          <view class="field">
            <text>毕业年份</text>
            <input v-model.number="profile.graduationYear" type="number" placeholder="2027" />
          </view>
        </view>
        <view class="field"><text>目标城市</text><input v-model="citiesText" placeholder="上海、杭州，多个用顿号分隔" /></view>
        <view class="field"><text>偏好行业</text><input v-model="industriesText" placeholder="互联网、金融科技" /></view>
        <view class="field"><text>已有技能</text><input v-model="skillsText" placeholder="Python、SQL、Excel，多个用顿号分隔" /></view>
        <view class="two-columns">
          <view class="field"><text>最低期望薪资</text><input v-model="profile.minimumSalary" placeholder="例如：10k" /></view>
          <view class="field"><text>工作形式</text><input v-model="profile.workTypes[0]" placeholder="全职 / 实习" /></view>
        </view>
        <text v-if="error" class="error">{{ error }}</text>
        <button class="primary" :loading="loading" @click="generatePlan">生成我的三档求职方案</button>
      </view>

      <template v-if="store.result">
        <view class="card report-card">
          <view class="section-heading"><text>专业匹配报告</text><text class="level">{{ majorReport?.matchingLevel }}</text></view>
          <text class="report-title">{{ majorReport?.major }} 的发展建议</text>
          <text v-for="item in majorReport?.matchingAdvantages" :key="item" class="bullet">优势：{{ item }}</text>
          <text v-for="item in majorReport?.missingSkills" :key="item" class="bullet warn">待补齐：{{ item }}</text>
          <view class="chip-row"><text v-for="item in majorReport?.recommendedCourses" :key="item" class="chip">{{ item }}</text></view>
        </view>

        <view class="tier-tabs">
          <view v-for="item in tierOptions" :key="item.key" class="tier-tab" :class="{ active: selectedTier === item.key }" @click="selectedTier = item.key">
            <text>{{ item.label }}</text><text>{{ item.hint }}</text>
          </view>
        </view>

        <view v-for="recommendation in recommendations" :key="recommendation.role.roleName" class="card role-card">
          <view class="role-top">
            <view><text class="role-name">{{ recommendation.role.roleName }}</text><text class="role-family">{{ recommendation.role.family }}</text></view>
            <view class="score"><text>{{ recommendation.totalScore }}</text><text>/100</text></view>
          </view>
          <text class="description">{{ recommendation.role.description }}</text>
          <view class="chip-row"><text v-for="item in recommendation.matchingAdvantages" :key="item" class="chip positive">{{ item }}</text></view>
          <text v-if="recommendation.missingSkills.length" class="gap">优先补齐：{{ recommendation.missingSkills.slice(0, 3).join("、") }}</text>
          <view class="score-list">
            <text v-for="score in recommendation.scoreBreakdown" :key="score.key">{{ score.label }} {{ score.score }}/{{ score.maxScore }} · {{ score.reason }}</text>
          </view>
          <view class="action-box">
            <text v-for="item in recommendation.actionPlan.slice(0, 3)" :key="item">- {{ item }}</text>
          </view>
          <button class="secondary" :loading="resumeLoading === recommendation.role.roleName" @click="useForResume(recommendation)">按此岗位优化简历</button>
        </view>
        <text class="notice">{{ store.result.recommendationNotice }}</text>
      </template>
    </view>
  </scroll-view>
</template>

<style scoped>
.page { min-height: 100vh; background: #f4f7fb; color: #1f2937; }
.content { padding: 24rpx 24rpx 52rpx; }
.hero { padding: 34rpx 20rpx 28rpx; background: linear-gradient(145deg, #e7f1ff, #f7fbff); border-radius: 24rpx; margin-bottom: 20rpx; }
.eyebrow { display: block; color: #1677ff; font-size: 21rpx; font-weight: 700; letter-spacing: 1rpx; }
.title { display: block; font-size: 44rpx; font-weight: 700; margin-top: 10rpx; }
.subtitle { display: block; color: #6b7280; line-height: 1.6; margin-top: 12rpx; font-size: 25rpx; }
.assessment-brief { display: flex; align-items: center; justify-content: space-between; gap: 20rpx; margin-top: 20rpx; padding: 20rpx 22rpx; background: #f0f7ff; border: 1rpx solid #cfe4fb; border-radius: 16rpx; }
.assessment-brief > view { min-width: 0; }.assessment-brief-title,.assessment-brief-text { display: block; }.assessment-brief-title { color: #245b99; font-size: 27rpx; font-weight: 700; }.assessment-brief-text { margin-top: 6rpx; color: #59728d; font-size: 22rpx; line-height: 1.5; }
.assessment-entry { flex-shrink: 0; margin: 0; padding: 0 22rpx; color: #1677ff; background: rgba(255,255,255,.82); border: 1rpx solid #a9d1ff; border-radius: 999rpx; font-size: 24rpx; line-height: 62rpx; }
.card { background: #fff; border: 1rpx solid #e7edf5; border-radius: 20rpx; padding: 24rpx; margin-top: 20rpx; box-shadow: 0 8rpx 24rpx rgba(35, 78, 130, 0.06); }
.section-heading, .role-top { display: flex; justify-content: space-between; align-items: center; gap: 16rpx; font-weight: 700; font-size: 30rpx; }
.hint, .level, .role-family { font-size: 22rpx; color: #6b7280; font-weight: 400; }
.field { margin-top: 20rpx; position: relative; }
.field > text { display: block; font-size: 24rpx; color: #4b5563; margin-bottom: 10rpx; }
input, .picker { box-sizing: border-box; min-height: 76rpx; width: 100%; padding: 0 20rpx; background: #f8fafc; border: 1rpx solid #dfe7f1; border-radius: 12rpx; font-size: 27rpx; line-height: 76rpx; }
.two-columns { display: grid; grid-template-columns: 1fr 1fr; gap: 18rpx; }
.suggestions { position: absolute; z-index: 5; top: 118rpx; left: 0; right: 0; background: #fff; border: 1rpx solid #dfe7f1; border-radius: 12rpx; overflow: hidden; box-shadow: 0 10rpx 30rpx rgba(30, 64, 105, .12); }
.suggestion { display: flex; justify-content: space-between; padding: 18rpx; border-bottom: 1rpx solid #eef2f7; font-size: 25rpx; }
.suggestion text:last-child { color: #86909c; font-size: 21rpx; }
button { margin-top: 24rpx; border-radius: 12rpx; font-size: 28rpx; }
.primary { background: #1677ff; color: #fff; }
.secondary { color: #1677ff; background: #e8f3ff; border: 1rpx solid #b9d9ff; }
.error, .gap { display: block; color: #d4380d; margin-top: 14rpx; font-size: 24rpx; }
.report-title { display: block; margin-top: 18rpx; font-size: 27rpx; font-weight: 600; }
.bullet { display: block; margin-top: 12rpx; color: #475569; font-size: 24rpx; line-height: 1.5; }
.warn { color: #c2410c; }
.chip-row { display: flex; flex-wrap: wrap; gap: 10rpx; margin-top: 16rpx; }
.chip { padding: 7rpx 12rpx; border-radius: 999rpx; background: #f1f5f9; color: #475569; font-size: 22rpx; }
.positive { background: #e8f3ff; color: #1677ff; }
.tier-tabs { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12rpx; margin-top: 20rpx; }
.tier-tab { padding: 16rpx 12rpx; background: #edf2f7; border-radius: 14rpx; color: #64748b; }
.tier-tab text { display: block; font-size: 22rpx; line-height: 1.35; }
.tier-tab text:first-child { font-size: 29rpx; font-weight: 700; margin-bottom: 5rpx; }
.tier-tab.active { background: #1677ff; color: #fff; box-shadow: 0 8rpx 18rpx rgba(22, 119, 255, .2); }
.role-name { display: block; font-size: 32rpx; }
.role-family { display: block; margin-top: 7rpx; }
.score { min-width: 86rpx; height: 86rpx; display: flex; flex-direction: column; justify-content: center; align-items: center; border-radius: 50%; background: #e8f3ff; color: #1677ff; }
.score text:first-child { font-size: 32rpx; font-weight: 700; }.score text:last-child { font-size: 19rpx; }
.description, .notice { display: block; margin-top: 16rpx; color: #64748b; font-size: 24rpx; line-height: 1.6; }
.score-list { padding: 14rpx 0; }.score-list text, .action-box text { display: block; margin-top: 8rpx; color: #64748b; line-height: 1.5; font-size: 22rpx; }
.action-box { margin-top: 10rpx; padding: 14rpx; border-radius: 12rpx; background: #f8fafc; }
.notice { padding: 8rpx 8rpx 0; font-size: 21rpx; }
</style>
