<script setup lang="ts">
import { Save, X } from "lucide-vue-next"

import AsyncButton from "./AsyncButton.vue"
import type { EvidenceDraft, EvidenceKind } from "../lib/evidence"

const props = defineProps<{
  modelValue: EvidenceDraft
  pending: boolean
  editing: boolean
}>()

const emit = defineEmits<{
  "update:modelValue": [value: EvidenceDraft]
  submit: []
  cancel: []
}>()

const kinds: Array<[EvidenceKind, string]> = [
  ["coursework", "课程学习"],
  ["project", "项目经历"],
  ["activity", "校园活动"],
  ["internship", "实习经历"],
  ["employment", "工作经历"],
]

function update<K extends keyof EvidenceDraft>(key: K, value: EvidenceDraft[K]): void {
  emit("update:modelValue", { ...props.modelValue, [key]: value } as EvidenceDraft)
}
</script>

<template>
  <form class="evidence-form" @submit.prevent="emit('submit')">
    <div class="editor-grid">
      <label><span>证据类型</span><select :value="modelValue.kind" @change="update('kind', ($event.target as HTMLSelectElement).value as EvidenceKind)"><option v-for="[value, label] in kinds" :key="value" :value="value">{{ label }}</option></select></label>
      <label><span>标题</span><input :value="modelValue.title" required maxlength="240" placeholder="例如：校园招聘项目" @input="update('title', ($event.target as HTMLInputElement).value)" /></label>
      <label class="editor-wide"><span>背景</span><textarea :value="modelValue.context" rows="2" maxlength="4000" placeholder="说明发生场景和目标" @input="update('context', ($event.target as HTMLTextAreaElement).value)" /></label>
      <label class="editor-wide"><span>行动</span><textarea :value="modelValue.actions" required rows="3" maxlength="8000" placeholder="你具体做了什么" @input="update('actions', ($event.target as HTMLTextAreaElement).value)" /></label>
      <label class="editor-wide"><span>结果</span><textarea :value="modelValue.outcome" rows="3" maxlength="4000" placeholder="尽量填写可观察结果" @input="update('outcome', ($event.target as HTMLTextAreaElement).value)" /></label>
      <label class="editor-wide"><span>证明备注</span><textarea :value="modelValue.proofNote" rows="2" maxlength="2000" placeholder="可核验材料或来源" @input="update('proofNote', ($event.target as HTMLTextAreaElement).value)" /></label>
    </div>
    <label class="evidence-verified"><input type="checkbox" :checked="modelValue.verified" @change="update('verified', ($event.target as HTMLInputElement).checked)" /><span>标记为已验证</span></label>
    <div class="heading-actions"><AsyncButton v-if="editing" class="text-action" type="button" @click="emit('cancel')"><X :size="15" aria-hidden="true" />取消编辑</AsyncButton><AsyncButton class="primary-button compact" type="submit" :loading="pending"><Save :size="16" aria-hidden="true" />{{ editing ? "保存修改" : "保存证据" }}</AsyncButton></div>
  </form>
</template>
