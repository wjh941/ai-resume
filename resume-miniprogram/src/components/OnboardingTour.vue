<script setup lang="ts">
import { computed, ref, watch } from "vue"

type Destination = "resume" | "career" | "applications"

const props = defineProps<{ visible: boolean }>()
const emit = defineEmits<{
  complete: []
  navigate: [destination: Destination]
}>()

const activeStep = ref(0)
const steps: Array<{ title: string; description: string; action: string; destination: Destination }> = [
  {
    title: "先完善简历",
    description: "填写基本信息、经历和技能，后续推荐会更贴合你的目标。",
    action: "前往简历编辑",
    destination: "resume",
  },
  {
    title: "生成职业规划",
    description: "选择目标方向，获取可执行的职业发展建议。",
    action: "前往职业规划",
    destination: "career",
  },
  {
    title: "管理投递进度",
    description: "记录每次投递、面试和后续安排，让求职进度更清晰。",
    action: "前往投递管理",
    destination: "applications",
  },
]

const currentStep = computed(() => steps[activeStep.value])
const isLastStep = computed(() => activeStep.value === steps.length - 1)

watch(
  () => props.visible,
  (visible) => {
    if (visible) activeStep.value = 0
  },
)

function next(): void {
  if (isLastStep.value) {
    emit("complete")
    return
  }
  activeStep.value += 1
}

function goToCurrentStep(): void {
  emit("navigate", currentStep.value.destination)
}
</script>

<template>
  <transition name="onboarding">
    <view v-if="visible" class="onboarding-mask" @click.self="emit('complete')">
      <view class="onboarding-dialog" role="dialog" aria-modal="true" aria-label="新手引导">
        <view class="onboarding-progress" aria-hidden="true">
          <view
            v-for="(_, index) in steps"
            :key="index"
            class="onboarding-progress-dot"
            :class="{ active: index <= activeStep }"
          />
        </view>
        <text class="onboarding-step">第 {{ activeStep + 1 }} 步，共 {{ steps.length }} 步</text>
        <text class="onboarding-title">{{ currentStep.title }}</text>
        <text class="onboarding-description">{{ currentStep.description }}</text>
        <view class="onboarding-actions">
          <button class="onboarding-secondary" @click="emit('complete')">跳过引导</button>
          <button class="onboarding-primary" @click="next">{{ isLastStep ? "完成引导" : "下一步" }}</button>
        </view>
        <button class="onboarding-link" @click="goToCurrentStep">{{ currentStep.action }}</button>
      </view>
    </view>
  </transition>
</template>

<style scoped>
.onboarding-mask { position: fixed; z-index: 1000; inset: 0; display: flex; align-items: flex-end; justify-content: center; padding: 32rpx; background: rgba(15, 23, 42, .42); }
.onboarding-dialog { width: 100%; max-width: 640rpx; padding: 32rpx; background: #fff; border: 1rpx solid rgba(203, 213, 225, .8); border-radius: 24rpx; box-shadow: 0 24rpx 64rpx rgba(15, 23, 42, .22); }
.onboarding-progress { display: flex; gap: 10rpx; }.onboarding-progress-dot { flex: 1; height: 8rpx; background: #e2e8f0; border-radius: 999rpx; transition: background-color .2s ease, transform .2s ease; }.onboarding-progress-dot.active { background: #2563eb; transform: scaleY(1.15); }
.onboarding-step,.onboarding-title,.onboarding-description { display: block; }.onboarding-step { margin-top: 24rpx; color: #64748b; font-size: 24rpx; }.onboarding-title { margin-top: 12rpx; color: #0f172a; font-size: 38rpx; font-weight: 700; line-height: 1.3; }.onboarding-description { margin-top: 14rpx; color: #475569; font-size: 27rpx; line-height: 1.65; }
.onboarding-actions { display: flex; gap: 16rpx; margin-top: 30rpx; }.onboarding-actions button { flex: 1; margin: 0; font-size: 27rpx; }.onboarding-secondary { color: #475569; background: #f8fafc; border: 1rpx solid #cbd5e1; }.onboarding-primary { color: #fff; background: #2563eb; border: 1rpx solid #2563eb; }.onboarding-link { width: 100%; margin-top: 16rpx; color: #2563eb; background: transparent; border: 0; font-size: 25rpx; }
.onboarding-enter-active,.onboarding-leave-active { transition: opacity .2s ease; }.onboarding-enter-active .onboarding-dialog,.onboarding-leave-active .onboarding-dialog { transition: transform .2s ease, opacity .2s ease; }.onboarding-enter-from,.onboarding-leave-to { opacity: 0; }.onboarding-enter-from .onboarding-dialog,.onboarding-leave-to .onboarding-dialog { opacity: 0; transform: translateY(24rpx); }
</style>
