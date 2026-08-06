<script setup lang="ts">
import { useResumeStore } from "../../stores/resume"
import type { TemplateId } from "../../types/resume"

const store = useResumeStore()

const templates: Array<{ id: TemplateId; name: string; description: string }> = [
  { id: "business", name: "简约商务版", description: "适合综合岗位与通用求职场景" },
  { id: "technology", name: "技术开发/测试版", description: "突出技术关键词与项目表达" },
  { id: "graduate", name: "应届生实习简洁版", description: "强调潜力、课程与实践经历" },
  { id: "analytics", name: "数据分析/运营精致版", description: "强调数据思维、复盘与业务结果" },
]

function chooseTemplate(templateId: TemplateId) {
  store.draft.templateId = templateId
  store.checkpoint()
  uni.navigateTo({ url: "/pages/resume-editor/index" })
}
</script>

<template>
  <scroll-view class="page" scroll-y>
    <view class="hero">
      <text class="title">选择简历模板</text>
      <text class="subtitle">已按目标岗位生成安全补缺内容，缺失的个人经历会保留为待补充。</text>
    </view>
    <view class="template-grid">
      <view v-for="template in templates" :key="template.id" class="template-card" :class="`card-${template.id}`" @click="chooseTemplate(template.id)">
        <view class="mini-header">
          <text>{{ store.draft.resume.basic.name || "待补充姓名" }}</text>
          <text>{{ store.draft.resume.job.targetRole || "目标岗位" }}</text>
        </view>
        <text class="template-name">{{ template.name }}</text>
        <text class="description">{{ template.description }}</text>
        <view class="mini-lines"><view /><view /><view /></view>
        <button class="primary" size="mini" @click.stop="chooseTemplate(template.id)">使用此模板</button>
      </view>
    </view>
  </scroll-view>
</template>

<style scoped>
.page { height: 100vh; padding: 32rpx; box-sizing: border-box; background: #f7f8fa; }
.hero { margin-bottom: 28rpx; }.title { display: block; color: #1f2329; font-size: 42rpx; font-weight: 700; }.subtitle { display: block; margin-top: 12rpx; color: #86909c; font-size: 25rpx; line-height: 1.6; }
.template-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 20rpx; }
.template-card { display: flex; flex-direction: column; gap: 16rpx; min-height: 340rpx; padding: 24rpx; background: #fff; border: 2rpx solid #e5e6eb; border-radius: 20rpx; box-shadow: 0 8rpx 24rpx rgba(31,35,41,.05); }
.mini-header { display: flex; flex-direction: column; gap: 6rpx; padding: 16rpx; color: #fff; background: #4e5969; border-radius: 12rpx; font-size: 22rpx; }.card-technology .mini-header { background: #1677ff; }.card-graduate .mini-header { background: #36cfc9; }.card-analytics .mini-header { background: #9254de; }
.template-name { color: #1f2329; font-size: 30rpx; font-weight: 700; }.description { min-height: 70rpx; color: #86909c; font-size: 23rpx; line-height: 1.5; }
.mini-lines { display: flex; flex-direction: column; gap: 10rpx; flex: 1; }.mini-lines view { height: 10rpx; background: #f2f3f5; border-radius: 999rpx; }.mini-lines view:nth-child(2) { width: 78%; }.mini-lines view:nth-child(3) { width: 58%; }
.primary { color: #fff; background: #1677ff; }
</style>
