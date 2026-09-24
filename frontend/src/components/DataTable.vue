<script setup lang="ts">
import type { Component } from 'vue'
import EmptyState from './EmptyState.vue'

defineOptions({ inheritAttrs: false })

defineProps<{
  loading?: boolean
  emptyTitle?: string
  emptyDescription?: string
  emptyActionText?: string
  emptyIcon?: Component
}>()

defineEmits<{ 'empty-action': [] }>()
</script>

<template>
  <div class="data-table">
    <div v-if="$slots.toolbar" class="dt-toolbar"><slot name="toolbar" /></div>

    <el-table v-bind="$attrs" v-loading="loading">
      <slot />
      <template #empty>
        <EmptyState
          :title="emptyTitle || '暂无数据'"
          :description="emptyDescription"
          :action-text="emptyActionText"
          :icon="emptyIcon"
          @action="$emit('empty-action')"
        />
      </template>
    </el-table>

    <div v-if="$slots.footer" class="dt-footer"><slot name="footer" /></div>
  </div>
</template>

<style scoped>
.data-table {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: var(--r-card);
  padding: 16px;
}
.dt-toolbar {
  margin-bottom: 0;
}
.dt-footer {
  margin-top: 12px;
}
</style>
