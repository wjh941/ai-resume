<script setup lang="ts">
import { LogOut, Moon, Sun } from "lucide-vue-next"

import type { SessionUser } from "../lib/session"

defineProps<{
  user: SessionUser
  dark: boolean
}>()

const emit = defineEmits<{
  logout: []
  toggleTheme: []
}>()
</script>

<template>
  <header class="web-topbar">
    <div class="topbar-status"><span class="status-dot" aria-hidden="true" />资料已连接，可继续完善求职计划</div>
    <div class="topbar-actions">
      <button
        class="icon-button"
        type="button"
        :title="dark ? '切换浅色界面' : '切换深色界面'"
        :aria-label="dark ? '切换浅色界面' : '切换深色界面'"
        @click="emit('toggleTheme')"
      >
        <Sun v-if="dark" :size="18" aria-hidden="true" />
        <Moon v-else :size="18" aria-hidden="true" />
      </button>
      <span class="user-chip"><b>{{ user.account || user.phone || "当前用户" }}</b><small>{{ user.role === "operator" ? "运营权限" : "求职者" }}</small></span>
      <button class="icon-button" type="button" title="退出登录" aria-label="退出登录" @click="emit('logout')">
        <LogOut :size="18" aria-hidden="true" />
      </button>
    </div>
  </header>
</template>
