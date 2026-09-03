<script setup lang="ts">
import { Download, RefreshCw, ShieldCheck, Trash2 } from "lucide-vue-next"
import { onMounted, ref } from "vue"

import { downloadApi, requestApi } from "../lib/api"
import { triggerBlobDownload } from "../lib/download-file"
import type { WorkspaceView } from "../components/WebSidebar.vue"
import AsyncButton from "../components/AsyncButton.vue"
import LoadingSpinner from "../components/LoadingSpinner.vue"

type DataScope = {
  categories: string[]
  retention_note: string
  privacy_policy_hint: string
}

const scope = ref<DataScope | null>(null)
const loading = ref(true)
const error = ref("")
const notice = ref("")
const pendingAction = ref<"consent" | "export" | "deletion" | "">("")
const emit = defineEmits<{
  navigate: [view: WorkspaceView]
  deleted: []
}>()

async function refresh() {
  loading.value = true
  error.value = ""
  try {
    scope.value = await requestApi<DataScope>("/api/account/data-scope")
  } catch {
    error.value = "暂时无法读取账户数据范围，请稍后重试"
  } finally {
    loading.value = false
  }
}

async function recordConsent() {
  if (pendingAction.value) return
  pendingAction.value = "consent"
  error.value = ""
  try {
    await requestApi("/api/account/privacy-consent", { method: "POST" })
    notice.value = "已记录你的隐私说明确认。"
  } catch {
    error.value = "确认状态未保存，请稍后重试"
  } finally {
    pendingAction.value = ""
  }
}

async function prepareExport() {
  if (pendingAction.value) return
  pendingAction.value = "export"
  error.value = ""
  try {
    const prepared = await requestApi<{ download_url?: string }>("/api/account/data-export", { method: "POST" })
    const archive = await downloadApi(prepared.download_url || "/api/account/data-export")
    triggerBlobDownload(archive, "ai-resume-account-data.zip")
    notice.value = "个人数据导出已下载。请妥善保管 ZIP 文件。"
  } catch {
    error.value = "数据导出暂时不可用，请稍后重试"
  } finally {
    pendingAction.value = ""
  }
}

async function requestDeletion() {
  if (pendingAction.value) return
  if (!window.confirm("删除申请会匿名化个人简历和职业资料，并且账户无法再次登录。确定继续吗？")) return
  pendingAction.value = "deletion"
  try {
    await requestApi("/api/account/deletion-request", { method: "POST" })
    emit("deleted")
  } catch {
    error.value = "删除申请未完成，请稍后重试"
  } finally {
    pendingAction.value = ""
  }
}

onMounted(refresh)
</script>

<template>
  <section class="view-layout">
    <div class="view-heading"><div><h1 id="account-title">账户设置</h1><p>了解当前账户的数据范围，并在需要时完成隐私确认、导出或删除申请。</p></div><AsyncButton class="text-action" type="button" :loading="loading" @click="refresh"><RefreshCw :size="16" aria-hidden="true" />重试读取</AsyncButton></div>
    <ErrorNotice v-if="error" :message="error" /><p v-if="notice" class="notice-success" aria-live="polite">{{ notice }}</p>
    <div v-if="loading" class="content-skeleton" aria-busy="true"><LoadingSpinner class="content-loading-spinner" label="正在读取账户数据范围" /><span /><span /></div>
    <article v-else-if="scope" class="account-scope workbench-form"><section><ShieldCheck :size="25" aria-hidden="true" /><div><h2>当前数据范围</h2><p>{{ scope.privacy_policy_hint }}</p></div></section><ul class="tag-list"><li v-for="category in scope.categories" :key="category">{{ category }}</li></ul><p class="source-notice">{{ scope.retention_note }}</p><div class="account-actions"><AsyncButton class="text-action" type="button" :disabled="Boolean(pendingAction)" @click="emit('navigate', 'membership')"><ShieldCheck :size="16" aria-hidden="true" />查看会员与订单</AsyncButton><AsyncButton class="text-action" type="button" :loading="pendingAction === 'consent'" :disabled="Boolean(pendingAction)" @click="recordConsent"><ShieldCheck :size="16" aria-hidden="true" />确认隐私说明</AsyncButton><AsyncButton class="text-action" type="button" :loading="pendingAction === 'export'" :disabled="Boolean(pendingAction)" @click="prepareExport"><Download :size="16" aria-hidden="true" />下载数据 ZIP</AsyncButton><AsyncButton class="danger-action" type="button" :loading="pendingAction === 'deletion'" :disabled="Boolean(pendingAction)" @click="requestDeletion"><Trash2 :size="16" aria-hidden="true" />申请删除账户</AsyncButton></div></article>
  </section>
</template>
