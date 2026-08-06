<script setup lang="ts">
import { computed, watch } from "vue"
import FormField from "../../components/FormField.vue"
import { saveDraft } from "../../services/resume-api"
import { useResumeStore } from "../../stores/resume"
import { getClientId } from "../../stores/session"
import { prepareResumeForJob } from "../../utils/resume-autofill"
import { validateResume } from "../../utils/validators"

const store = useResumeStore()
const resume = computed(() => store.draft.resume)
watch(() => store.draft, () => store.checkpoint(), { deep: true })

function addEducation() { resume.value.education.push({ school: "", major: "", degree: "", startDate: "", endDate: "", courses: "" }); store.checkpoint() }
function addEmployment() { resume.value.employment.push({ company: "", position: "", startDate: "", endDate: "", description: "" }); store.checkpoint() }
function addProject() { resume.value.projects.push({ name: "", role: "", startDate: "", endDate: "", description: "" }); store.checkpoint() }

async function save() {
  const errors = validateResume(resume.value)
  if (errors.length) return uni.showToast({ title: errors[0].message, icon: "none" })
  try {
    const saved = await saveDraft(getClientId(), store.draft)
    store.draft.id = saved.id
    store.checkpoint()
    uni.showToast({ title: "草稿已保存", icon: "success" })
  } catch {
    store.checkpoint()
    uni.showToast({ title: "网络异常，已保留本地草稿", icon: "none" })
  }
}

function prepareAndChooseTemplate() {
  const job = store.activeJob ?? store.draft.jobIntelligence
  if (!job) {
    uni.showToast({ title: "请先查询目标岗位", icon: "none" })
    return
  }
  prepareResumeForJob(store.draft, job)
  store.checkpoint()
  uni.navigateTo({ url: "/pages/template-picker/index" })
}
</script>

<template>
  <scroll-view class="page" scroll-y>
    <view class="card"><text class="heading">个人信息</text>
      <FormField label="姓名" v-model="resume.basic.name" placeholder="请输入姓名" />
      <FormField label="手机号码" v-model="resume.basic.phone" placeholder="请输入手机号码" />
      <FormField label="邮箱" v-model="resume.basic.email" placeholder="请输入邮箱" />
      <FormField label="所在城市" v-model="resume.basic.city" placeholder="请输入城市" />
    </view>
    <view class="card"><text class="heading">求职信息</text>
      <FormField label="期望岗位" v-model="resume.job.targetRole" placeholder="例如：数据工程师" />
      <FormField label="期望薪资" v-model="resume.job.expectedSalary" placeholder="例如：20k-30k" />
      <FormField label="到岗时间" v-model="resume.job.availability" placeholder="例如：两周内" />
    </view>
    <view class="card"><view class="row"><text class="heading">教育经历</text><button size="mini" @click="addEducation">新增</button></view>
      <view v-for="(item, index) in resume.education" :key="index" class="entry"><FormField label="学校" v-model="item.school" /><FormField label="专业" v-model="item.major" /><button size="mini" @click="resume.education.splice(index, 1)">删除</button></view>
    </view>
    <view class="card"><view class="row"><text class="heading">实习/工作经历</text><button size="mini" @click="addEmployment">新增</button></view>
      <view v-for="(item, index) in resume.employment" :key="index" class="entry"><FormField label="公司" v-model="item.company" /><FormField label="岗位" v-model="item.position" /><textarea v-model="item.description" placeholder="工作描述" /><button size="mini" @click="resume.employment.splice(index, 1)">删除</button></view>
    </view>
    <view class="card"><view class="row"><text class="heading">项目经历</text><button size="mini" @click="addProject">新增</button></view>
      <view v-for="(item, index) in resume.projects" :key="index" class="entry"><FormField label="项目名称" v-model="item.name" /><FormField label="角色" v-model="item.role" /><textarea v-model="item.description" placeholder="项目描述与成果" /><button size="mini" @click="resume.projects.splice(index, 1)">删除</button></view>
    </view>
    <view class="card"><FormField label="技能（以逗号分隔）" :model-value="resume.skills.skills.join(',')" @update:model-value="resume.skills.skills = $event.split(',').map(item => item.trim()).filter(Boolean)" /><textarea v-model="resume.selfEvaluation" placeholder="自我评价" /></view>
    <view class="actions"><button @click="save">保存草稿</button><button class="primary" @click="prepareAndChooseTemplate">智能补全并选择模板</button></view>
  </scroll-view>
</template>

<style scoped>
.page { height: 100vh; padding: 24rpx; box-sizing: border-box; }.card { margin-bottom: 20rpx; padding: 24rpx; background: #fff; border-radius: 16rpx; }.heading { font-size: 32rpx; font-weight: 600; }.row { display: flex; justify-content: space-between; align-items: center; }.entry { margin-top: 18rpx; padding-top: 12rpx; border-top: 1px solid #f2f3f5; } textarea { width: 100%; min-height: 130rpx; margin: 16rpx 0; padding: 16rpx; background: #f7f8fa; border-radius: 12rpx; }.actions { display: flex; gap: 16rpx; padding-bottom: 48rpx; }.actions button { flex: 1; }.primary { color: #fff; background: #1677ff; }
</style>
