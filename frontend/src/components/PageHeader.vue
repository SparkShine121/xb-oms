<script setup lang="ts">
defineProps<{ title: string; sub?: string }>()
</script>

<template>
  <div class="page-header">
    <h2 class="ph-title">{{ title }}</h2>
    <span v-if="sub" class="ph-sub">{{ sub }}</span>
    <div class="ph-actions"><slot /></div>
  </div>
</template>

<style scoped>
.page-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 14px;
}
.ph-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  letter-spacing: -0.01em;
  color: var(--txt);
}
.ph-sub {
  font-size: 12.5px;
  color: var(--mut);
}
.ph-actions {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>
