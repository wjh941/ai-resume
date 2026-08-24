<script setup lang="ts">
import {
  BarChart3,
  BriefcaseBusiness,
  ChartNoAxesCombined,
  ClipboardCheck,
  FilePenLine,
  Home,
  Crown,
  GitCompareArrows,
  KanbanSquare,
  Map,
  UserRound,
} from "lucide-vue-next"

export type WorkspaceView =
  | "overview"
  | "resume"
  | "career"
  | "jobs"
  | "applications"
  | "evidence"
  | "membership"
  | "assessment"
  | "comparison"
  | "insights"
  | "account"

defineProps<{
  activeView: WorkspaceView
}>()

const emit = defineEmits<{
  navigate: [view: WorkspaceView]
}>()

const navigation = [
  { key: "overview", label: "工作概览", icon: Home },
  { key: "resume", label: "简历中心", icon: FilePenLine },
  { key: "career", label: "职业规划", icon: Map },
  { key: "jobs", label: "岗位机会", icon: BriefcaseBusiness },
  { key: "applications", label: "投递管理", icon: KanbanSquare },
  { key: "evidence", label: "经历证据", icon: ClipboardCheck },
  { key: "membership", label: "会员与订单", icon: Crown },
  { key: "assessment", label: "职业测评", icon: ChartNoAxesCombined },
  { key: "comparison", label: "岗位对比", icon: GitCompareArrows },
  { key: "insights", label: "年度洞察", icon: ChartNoAxesCombined },
  { key: "account", label: "账户设置", icon: UserRound },
] as const
</script>

<template>
  <aside class="web-sidebar" aria-label="主导航">
    <div class="brand-lockup">
      <span class="brand-symbol" aria-hidden="true"><BarChart3 :size="22" /></span>
      <span><strong>求职成长</strong><small>行动工作台</small></span>
    </div>

    <nav class="workspace-navigation">
      <button
        v-for="item in navigation"
        :key="item.key"
        class="navigation-item"
        :class="{ 'is-active': activeView === item.key }"
        type="button"
        :aria-current="activeView === item.key ? 'page' : undefined"
        @click="emit('navigate', item.key)"
      >
        <component :is="item.icon" :size="19" stroke-width="1.8" aria-hidden="true" />
        <span>{{ item.label }}</span>
      </button>
    </nav>

    <p class="sidebar-note">把信息变成下一步行动</p>
  </aside>
</template>
