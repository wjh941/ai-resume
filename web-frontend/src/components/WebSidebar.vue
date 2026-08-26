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
  ChevronDown,
} from "lucide-vue-next"
import { computed, onMounted, onUnmounted, ref } from "vue"

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

const props = defineProps<{
  activeView: WorkspaceView
}>()

const emit = defineEmits<{
  navigate: [view: WorkspaceView]
}>()

const navigationGroups = [
  {
    label: "准备资料",
    items: [
      { key: "overview", label: "工作概览", icon: Home },
      { key: "resume", label: "简历中心", icon: FilePenLine },
      { key: "evidence", label: "经历证据", icon: ClipboardCheck },
    ],
  },
  {
    label: "职业决策",
    items: [
      { key: "career", label: "职业规划", icon: Map },
      { key: "assessment", label: "职业测评", icon: ChartNoAxesCombined },
      { key: "comparison", label: "岗位对比", icon: GitCompareArrows },
    ],
  },
  {
    label: "求职执行",
    items: [
      { key: "jobs", label: "岗位机会", icon: BriefcaseBusiness },
      { key: "applications", label: "投递管理", icon: KanbanSquare },
    ],
  },
  {
    label: "复盘与账户",
    items: [
      { key: "insights", label: "年度洞察", icon: ChartNoAxesCombined },
      { key: "membership", label: "会员与订单", icon: Crown },
      { key: "account", label: "账户设置", icon: UserRound },
    ],
  },
] as const

const drawerOpen = ref(false)
const collapsedGroups = ref<Record<string, boolean>>({})
const totalItems = navigationGroups.reduce((count, group) => count + group.items.length, 0)
const activeIndex = computed(() => Math.max(0, navigationGroups.flatMap((group) => group.items).findIndex((item) => item.key === props.activeView)))
const workspaceProgress = computed(() => Math.round(((activeIndex.value + 1) / totalItems) * 100))

function toggleDrawer(): void { drawerOpen.value = !drawerOpen.value }
function closeDrawer(): void { drawerOpen.value = false }
function toggleGroup(label: string): void { collapsedGroups.value[label] = !collapsedGroups.value[label] }
function isGroupCollapsed(label: string): boolean { return Boolean(collapsedGroups.value[label]) }
function navigateTo(view: WorkspaceView): void { emit("navigate", view); closeDrawer() }
function onKeydown(event: KeyboardEvent): void { if (event.key === "Escape") closeDrawer() }

onMounted(() => window.addEventListener("keydown", onKeydown))
onUnmounted(() => window.removeEventListener("keydown", onKeydown))
</script>

<template>
  <aside class="web-sidebar" :class="{ 'is-drawer-open': drawerOpen }" aria-label="主导航">
    <div class="sidebar-mobile-bar">
      <button class="sidebar-toggle" type="button" :aria-expanded="drawerOpen" :aria-label="drawerOpen ? '关闭导航' : '打开导航'" @click="toggleDrawer">
        <svg class="sidebar-toggle-icon" viewBox="0 0 24 24" aria-hidden="true"><path class="sidebar-toggle-line sidebar-toggle-line-one" d="M4 7h16" /><path class="sidebar-toggle-line sidebar-toggle-line-two" d="M4 12h16" /><path class="sidebar-toggle-line sidebar-toggle-line-three" d="M4 17h16" /></svg>
      </button>
      <span class="sidebar-mobile-title">工作台导航</span>
      <strong>{{ workspaceProgress }}%</strong>
    </div>
    <button v-if="drawerOpen" class="sidebar-drawer-backdrop" type="button" aria-label="关闭导航" @click="closeDrawer" />
    <div class="brand-lockup">
      <span class="brand-symbol" aria-hidden="true"><BarChart3 :size="22" /></span>
      <span><strong>求职成长</strong><small>行动工作台</small></span>
    </div>

    <nav class="workspace-navigation">
      <div v-for="group in navigationGroups" :key="group.label" class="navigation-group" :class="{ 'is-collapsed': isGroupCollapsed(group.label) }" role="group" :aria-label="group.label">
        <button class="navigation-group-toggle" type="button" :aria-expanded="!isGroupCollapsed(group.label)" @click="toggleGroup(group.label)">
          <span class="navigation-group-label">{{ group.label }}</span><ChevronDown :size="15" aria-hidden="true" />
        </button>
        <Transition name="group-swipe">
          <div v-if="!isGroupCollapsed(group.label)" class="navigation-group-items">
            <button v-for="item in group.items" :key="item.key" class="navigation-item" :class="{ 'is-active': activeView === item.key }" type="button" :aria-current="activeView === item.key ? 'page' : undefined" @click="navigateTo(item.key)">
              <component :is="item.icon" :size="19" stroke-width="1.8" aria-hidden="true" /><span>{{ item.label }}</span>
            </button>
          </div>
        </Transition>
      </div>
    </nav>

    <div class="sidebar-progress liquid-slider" aria-label="当前工作台进度"><div><span>工作台进度</span><strong>{{ workspaceProgress }}%</strong></div><span class="liquid-slider-track"><span class="liquid-slider-fill" :style="{ '--progress-scale': workspaceProgress / 100 }" /></span></div>

    <p class="sidebar-note">把信息变成下一步行动</p>
  </aside>
</template>
