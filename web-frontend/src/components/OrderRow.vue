<script setup lang="ts">
import type { MembershipOrder } from "../lib/membership"

defineProps<{ order: MembershipOrder }>()
</script>

<template>
  <article class="order-row"><div><strong>{{ order.packageType }}</strong><small>{{ order.createTime }}</small></div><span class="status-tag">{{ order.paymentStatus }}</span><span>¥{{ order.totalAmount }}</span><small>{{ order.entitlementExpireTime || "待支付" }}</small></article>
</template>
