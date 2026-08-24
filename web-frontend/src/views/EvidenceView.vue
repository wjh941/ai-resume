<script setup lang="ts">
import { CheckCircle2, ClipboardCheck, FileSearch, Lightbulb, Plus, RefreshCw, Trash2 } from "lucide-vue-next"
import { onMounted, ref } from "vue"

import AsyncButton from "../components/AsyncButton.vue"
import EvidenceForm from "../components/EvidenceForm.vue"
import ExpandableText from "../components/ExpandableText.vue"
import LoadingSpinner from "../components/LoadingSpinner.vue"
import { listDrafts, type DraftRecord } from "../lib/drafts"
import { checkResumeReadiness, deleteEvidence, getEvidenceSuggestions, listEvidence, saveEvidence, type EvidenceDraft, type EvidenceRecord, type EvidenceSuggestion, type ResumeReadinessReport } from "../lib/evidence"
import { removeEvidence, replaceEvidence } from "../lib/evidence-workflow"

const emptyDraft = (): EvidenceDraft => ({ kind: "project", title: "", context: "", actions: "", outcome: "", proofNote: "", verified: false })
const kindLabels: Record<EvidenceRecord["kind"], string> = { coursework: "课程学习", project: "项目经历", activity: "校园活动", internship: "实习经历", employment: "工作经历" }
const items = ref<EvidenceRecord[]>([])
const drafts = ref<DraftRecord[]>([])
const model = ref<EvidenceDraft>(emptyDraft())
const editingId = ref<string | null>(null)
const loading = ref(true)
const saving = ref(false)
const pendingDelete = ref("")
const error = ref("")
const notice = ref("")
const roleName = ref("")
const suggestions = ref<EvidenceSuggestion[]>([])
const suggestionsLoading = ref(false)
const selectedDraftId = ref("")
const readiness = ref<ResumeReadinessReport | null>(null)
const readinessLoading = ref(false)

function resetForm(): void { editingId.value = null; model.value = emptyDraft() }
function clone<T>(value: T): T { return JSON.parse(JSON.stringify(value)) as T }
async function refresh(): Promise<void> {
  loading.value = true; error.value = ""
  try { const [evidence, draftList] = await Promise.all([listEvidence(), listDrafts()]); items.value = evidence; drafts.value = draftList } catch { error.value = "暂时无法读取经历证据，请稍后重试" } finally { loading.value = false }
}
function startEdit(item: EvidenceRecord): void { editingId.value = item.id; model.value = clone({ id: item.id, kind: item.kind, title: item.title, context: item.context, actions: item.actions, outcome: item.outcome, proofNote: item.proofNote, verified: item.verified }) }
async function submit(): Promise<void> {
  if (!model.value.title.trim() || !model.value.actions.trim() || saving.value) return
  saving.value = true; error.value = ""; notice.value = ""
  try { const saved = await saveEvidence({ ...model.value, id: editingId.value || undefined }); items.value = editingId.value ? replaceEvidence(items.value, saved) : [saved, ...items.value]; notice.value = editingId.value ? "经历证据已更新" : "经历证据已保存"; resetForm() } catch { error.value = "证据暂未保存，请检查填写内容后重试" } finally { saving.value = false }
}
async function remove(item: EvidenceRecord): Promise<void> {
  if (pendingDelete.value || !window.confirm("确认删除这条经历证据吗？")) return
  pendingDelete.value = item.id; error.value = ""
  try { await deleteEvidence(item.id); items.value = removeEvidence(items.value, item.id); if (editingId.value === item.id) resetForm() } catch { error.value = "证据暂未删除，请稍后重试" } finally { pendingDelete.value = "" }
}
async function loadSuggestions(): Promise<void> {
  if (!roleName.value.trim() || suggestionsLoading.value) return
  suggestionsLoading.value = true; error.value = ""
  try { suggestions.value = await getEvidenceSuggestions(roleName.value.trim()) } catch { error.value = "暂时无法生成证据建议，请稍后重试" } finally { suggestionsLoading.value = false }
}
async function checkReadiness(): Promise<void> {
  if (readinessLoading.value) return
  const draft = drafts.value.find((item) => item.id === selectedDraftId.value)
  if (!draft) { readiness.value = null; error.value = "请先选择一份简历草稿，再检查准备度"; return }
  readinessLoading.value = true; error.value = ""
  try { readiness.value = await checkResumeReadiness(draft.resume) } catch { error.value = "暂时无法检查简历准备度，请稍后重试" } finally { readinessLoading.value = false }
}
onMounted(refresh)
</script>

<template>
  <section class="view-layout evidence-view">
    <div class="view-heading"><div><h1 id="evidence-title">经历证据</h1><p>把项目、学习和工作经历沉淀为可复用的事实材料，帮助简历和面试表达更可信。</p></div><AsyncButton class="text-action" type="button" :loading="loading" @click="refresh"><RefreshCw :size="16" aria-hidden="true" />刷新</AsyncButton></div>
    <ErrorNotice v-if="error" :message="error" /><p v-if="notice" class="notice-success" aria-live="polite"><CheckCircle2 :size="16" aria-hidden="true" />{{ notice }}</p>
    <div v-if="loading" class="content-skeleton evidence-loading" aria-busy="true"><LoadingSpinner class="content-loading-spinner" label="正在读取经历证据" /><span /><span /><span /></div>
    <template v-else>
      <EvidenceForm v-model="model" :pending="saving" :editing="Boolean(editingId)" @submit="submit" @cancel="resetForm" />
      <div class="evidence-workspace-grid">
        <section class="evidence-panel"><div class="panel-heading"><div><span class="section-kicker"><ClipboardCheck :size="14" aria-hidden="true" />事实材料</span><h2>已保存证据</h2></div><AsyncButton class="text-action compact" type="button" @click="resetForm"><Plus :size="15" aria-hidden="true" />新增</AsyncButton></div><div v-if="items.length" class="evidence-list"><article v-for="item in items" :key="item.id"><div class="evidence-row-heading"><div><strong>{{ item.title }}</strong><small>{{ kindLabels[item.kind] }}<template v-if="item.verified"> · 已验证</template></small></div><div class="record-actions"><AsyncButton class="text-action compact" type="button" @click="startEdit(item)">编辑</AsyncButton><AsyncButton class="danger-action compact" type="button" :loading="pendingDelete === item.id" :disabled="Boolean(pendingDelete)" @click="remove(item)"><Trash2 :size="14" aria-hidden="true" />删除</AsyncButton></div></div><p><ExpandableText :text="item.actions" :lines="4" :expand-at="96" label="行动内容" /></p><small v-if="item.outcome">结果：{{ item.outcome }}</small></article></div><div v-else class="empty-board"><FileSearch :size="28" aria-hidden="true" /><div><h2>还没有证据材料</h2><p>从一段具体经历开始，记录背景、行动和结果。</p></div></div></section>
        <aside class="evidence-side-panels">
          <section class="evidence-panel"><div class="panel-heading"><div><span class="section-kicker"><Lightbulb :size="14" aria-hidden="true" />表达建议</span><h2>岗位匹配建议</h2></div></div><div class="suggestion-query"><label><span>目标岗位</span><input v-model.trim="roleName" maxlength="160" placeholder="例如：数据分析师" /></label><AsyncButton class="primary-button compact" type="button" :loading="suggestionsLoading" @click="loadSuggestions">生成建议</AsyncButton></div><div v-if="suggestions.length" class="suggestion-list"><article v-for="item in suggestions" :key="item.sourceEvidenceId + item.title"><strong>{{ item.title }}</strong><small>{{ item.sourceTitle }} · {{ item.targetSection === "project" ? "项目经历" : "工作经历" }}</small><p>{{ item.description }}</p><p v-if="item.riskNote" class="upgrade-notice">注意：{{ item.riskNote }}</p></article></div><p v-else class="source-notice">输入岗位后生成基于已保存证据的表达建议。</p></section>
          <section class="evidence-panel"><div class="panel-heading"><div><span class="section-kicker"><FileSearch :size="14" aria-hidden="true" />简历检查</span><h2>准备度</h2></div></div><label class="readiness-select"><span>选择简历草稿</span><select v-model="selectedDraftId"><option value="">请选择</option><option v-for="draft in drafts" :key="draft.id" :value="draft.id">{{ draft.jobTitle }}</option></select></label><AsyncButton class="text-action" type="button" :loading="readinessLoading" :disabled="!selectedDraftId" @click="checkReadiness">检查准备度</AsyncButton><div v-if="readiness" class="readiness-result" :class="{ 'is-ready': readiness.ready }"><strong>{{ readiness.ready ? "简历已具备基础完整度" : "还有内容需要补齐" }}</strong><ul v-if="readiness.blockingItems.length"><li v-for="item in readiness.blockingItems" :key="item">{{ item }}</li></ul><p v-if="readiness.warningItems.length">提醒：{{ readiness.warningItems.join("；") }}</p></div><p v-else class="source-notice">选择草稿后检查必填信息、经历完整度和风险提醒。</p></section>
        </aside>
      </div>
    </template>
  </section>
</template>
