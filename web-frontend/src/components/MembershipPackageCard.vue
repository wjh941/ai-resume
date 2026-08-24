<script setup lang="ts">
import { Check, Crown } from "lucide-vue-next"

import AsyncButton from "./AsyncButton.vue"
import type { MembershipPackage, VipStatus } from "../lib/membership"

defineProps<{
  package: MembershipPackage
  currentVip: VipStatus | null
  pending: boolean
}>()

const emit = defineEmits<{ purchase: [packageType: MembershipPackage["packageType"], autoRenew: boolean] }>()
</script>

<template>
  <article class="membership-package" :class="{ 'is-current': currentVip?.vipLevel === package.vipLevel }">
    <div class="package-heading"><span class="record-symbol record-coral"><Crown :size="20" aria-hidden="true" /></span><div><h3>{{ package.name }}</h3><p>{{ package.durationDays }} 天 · {{ package.vipLevel }}</p></div></div>
    <strong class="package-price">¥{{ package.totalAmount }}</strong>
    <ul class="package-benefits"><li v-for="benefit in package.benefits" :key="benefit"><Check :size="14" aria-hidden="true" />{{ benefit }}</li></ul>
    <AsyncButton class="primary-button compact" type="button" :loading="pending" @click="emit('purchase', package.packageType, false)">购买 {{ package.name }}</AsyncButton>
  </article>
</template>
