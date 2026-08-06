<script setup lang="ts">
import { computed } from "vue"

import type { ResumePayload, TemplateId } from "../types/resume"
import { previewContact } from "../utils/resume-preview"

const props = defineProps<{
  resume: ResumePayload
  templateId: TemplateId
}>()

const skills = computed(() => props.resume.skills.skills.filter(Boolean))

function dateRange(startDate: string, endDate: string): string {
  return [startDate, endDate].filter(Boolean).join(" - ")
}
</script>

<template>
  <view class="resume-preview" :class="`template-${templateId}`">
    <view v-if="resume.sectionVisibility.basic" class="resume-header">
      <text class="name">{{ previewContact(resume.basic.name, "待补充姓名") }}</text>
      <text class="contact">
        {{ previewContact(resume.basic.phone, "手机待补充") }} ｜ {{ previewContact(resume.basic.email, "邮箱待补充") }} ｜ {{ previewContact(resume.basic.city, "城市待补充") }}
      </text>
    </view>

    <view v-if="resume.sectionVisibility.job" class="section">
      <text class="section-title">求职目标</text>
      <text>目标岗位：{{ previewContact(resume.job.targetRole, "待补充岗位") }}</text>
      <text>期望薪资：{{ previewContact(resume.job.expectedSalary, "待补充") }}</text>
      <text>到岗时间：{{ previewContact(resume.job.availability, "待补充") }}</text>
    </view>

    <view v-if="resume.sectionVisibility.skills && skills.length" class="section">
      <text class="section-title">技能关键词</text>
      <view class="skill-list">
        <text v-for="skill in skills" :key="skill" class="skill">{{ skill }}</text>
      </view>
    </view>

    <view v-if="resume.sectionVisibility.selfEvaluation && resume.selfEvaluation.trim()" class="section">
      <text class="section-title">自我评价</text>
      <text>{{ resume.selfEvaluation }}</text>
    </view>

    <view v-if="resume.sectionVisibility.education && resume.education.length" class="section">
      <text class="section-title">教育经历</text>
      <view v-for="(item, index) in resume.education" :key="`${item.school}-${index}`" class="experience">
        <view class="experience-title">
          <text>{{ previewContact(item.school, "学校待补充") }}</text>
          <text>{{ dateRange(item.startDate, item.endDate) }}</text>
        </view>
        <text>{{ [item.major, item.degree].filter(Boolean).join(" ｜ ") }}</text>
        <text v-if="item.courses">{{ item.courses }}</text>
      </view>
    </view>

    <view v-if="resume.sectionVisibility.employment && resume.employment.length" class="section">
      <text class="section-title">实习/工作经历</text>
      <view v-for="(item, index) in resume.employment" :key="`${item.company}-${index}`" class="experience">
        <view class="experience-title">
          <text>{{ previewContact(item.company, "公司待补充") }}</text>
          <text>{{ dateRange(item.startDate, item.endDate) }}</text>
        </view>
        <text>{{ previewContact(item.position, "岗位待补充") }}</text>
        <text v-if="item.description">{{ item.description }}</text>
      </view>
    </view>

    <view v-if="resume.sectionVisibility.projects && resume.projects.length" class="section">
      <text class="section-title">项目经历</text>
      <view v-for="(item, index) in resume.projects" :key="`${item.name}-${index}`" class="experience">
        <view class="experience-title">
          <text>{{ previewContact(item.name, "项目名称待补充") }}</text>
          <text>{{ dateRange(item.startDate, item.endDate) }}</text>
        </view>
        <text>{{ previewContact(item.role, "角色待补充") }}</text>
        <text v-if="item.description">{{ item.description }}</text>
      </view>
    </view>
  </view>
</template>

<style scoped>
.resume-preview { padding: 40rpx 32rpx; background: #fff; color: #1f2329; border-radius: 20rpx; box-shadow: 0 16rpx 40rpx rgba(31, 35, 41, .08); }
.resume-header { padding-bottom: 28rpx; border-bottom: 2rpx solid #e5e6eb; }
.name { display: block; font-size: 48rpx; font-weight: 700; }
.contact { display: block; margin-top: 12rpx; color: #86909c; font-size: 24rpx; }
.section { display: flex; flex-direction: column; gap: 12rpx; margin-top: 32rpx; color: #4e5969; line-height: 1.65; }
.section-title { color: #1f2329; font-size: 30rpx; font-weight: 700; }
.skill-list { display: flex; flex-wrap: wrap; gap: 12rpx; }
.skill { padding: 8rpx 14rpx; color: #1677ff; background: #e8f3ff; border-radius: 999rpx; font-size: 23rpx; }
.experience { display: flex; flex-direction: column; gap: 6rpx; padding: 16rpx 0; border-top: 1rpx solid #f2f3f5; }
.experience-title { display: flex; justify-content: space-between; gap: 20rpx; color: #1f2329; font-weight: 600; }
.template-technology .resume-header { border-color: #1677ff; }.template-technology .section-title { color: #1677ff; }
.template-graduate .resume-header { border-color: #36cfc9; }.template-graduate .section-title { color: #08979c; }
.template-analytics .resume-header { border-color: #9254de; }.template-analytics .section-title { color: #722ed1; }
</style>
