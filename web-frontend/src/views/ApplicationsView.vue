<script setup lang="ts">
import { Building2, Plus, RefreshCw } from "lucide-vue-next"
import { onMounted, ref } from "vue"

import { requestApi } from "../lib/api"

type Application = {
  id: string
  company: string
  role_name: string
  city?: string
  status: string
  next_interview_at?: string | null
  next_action_at?: string | null
}

const items = ref<Application[]>([])
const company = ref("")
const roleName = ref("")
const city = ref("")
const status = ref("saved")
const loading = ref(true)
const saving = ref(false)
const error = ref("")

const statusLabels: Record<string, string> = {
  saved: "待投递",
  applied: "已投递",
  screening: "筛选中",
  interview: "面试中",
  offer: "已获录用",
  rejected: "未通过",
  closed: "已结束",
}

async function refresh() {
  loading.value = true
  error.value = ""
  try {
    items.value = (await requestApi<{ items: Application[] }>("/api/applications")).items
  } catch {
    error.value = "暂时无法读取投递记录，请稍后重试"
  } finally {
    loading.value = false
  }
}

async function addApplication() {
  if (!roleName.value.trim()) {
    error.value = "请填写投递岗位"
    return
  }
  saving.value = true
  error.value = ""
  try {
    const record = await requestApi<Application>("/api/applications", {
      method: "POST",
      body: JSON.stringify({ company: company.value.trim() || "[待确认]", role_name: roleName.value.trim(), city: city.value.trim(), status: status.value }),
    })
    items.value = [record, ...items.value]
    company.value = ""
    roleName.value = ""
    city.value = ""
    status.value = "saved"
  } catch {
    error.value = "投递记录暂未保存，请稍后重试"
  } finally {
    saving.value = false
  }
}

onMounted(refresh)
</script>

<template>
  <section class="view-layout">
    <div class="view-heading"><div><h1>投递管理</h1><p>保存投递意向、跟进状态和面试安排，让每一次行动都可复盘。</p></div><button class="text-action" type="button" :disabled="loading" @click="refresh"><RefreshCw :size="16" aria-hidden="true" />刷新</button></div>
    <form class="application-form" @submit.prevent="addApplication">
      <label><span>公司</span><input v-model.trim="company" maxlength="200" placeholder="例如：示例科技" /></label>
      <label><span>岗位</span><input v-model.trim="roleName" required maxlength="160" placeholder="例如：产品运营" /></label>
      <label><span>城市</span><input v-model.trim="city" maxlength="120" placeholder="例如：上海" /></label>
      <label><span>状态</span><select v-model="status"><option value="saved">待投递</option><option value="applied">已投递</option><option value="screening">筛选中</option><option value="interview">面试中</option><option value="offer">已获录用</option></select></label>
      <button class="primary-button compact" type="submit" :disabled="saving"><Plus :size="17" aria-hidden="true" />{{ saving ? "保存中" : "新增记录" }}</button>
    </form>
    <p v-if="error" class="notice-error" role="alert">{{ error }}</p>
    <div v-else-if="loading" class="content-skeleton" aria-busy="true"><span /><span /></div>
    <div v-else-if="items.length" class="application-table">
      <article v-for="item in items" :key="item.id" class="application-row"><span class="record-symbol record-sky"><Building2 :size="20" aria-hidden="true" /></span><div><h2>{{ item.role_name }}</h2><p>{{ item.company }}<template v-if="item.city"> · {{ item.city }}</template></p></div><span class="status-tag">{{ statusLabels[item.status] || item.status }}</span><small>{{ item.next_interview_at || item.next_action_at || "尚未设置下一步" }}</small></article>
    </div>
    <div v-else class="empty-board"><Building2 :size="30" aria-hidden="true" /><div><h2>还没有投递记录</h2><p>在确认岗位与公司信息后，先保存一条待投递记录，再持续补充状态和复盘信息。</p></div></div>
  </section>
</template>
