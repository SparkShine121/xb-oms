<script setup lang="ts">
import type { Component } from 'vue'
import { PhTray } from '@phosphor-icons/vue'

withDefaults(defineProps<{
  title: string
  description?: string
  actionText?: string
  icon?: Component
}>(), {
  icon: () => PhTray,
})

defineEmits<{ action: [] }>()
</script>

<template>
  <div class="empty-state">
    <component :is="icon" :size="48" weight="duotone" class="es-icon" aria-hidden="true" />
    <p class="es-title">{{ title }}</p>
    <p v-if="description" class="es-desc">{{ description }}</p>
    <el-button v-if="actionText" type="primary" @click="$emit('action')">{{ actionText }}</el-button>
  </div>
</template>

<style scoped>
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 36px 16px;
}
.es-icon {
  color: var(--dim);
}
.es-title {
  margin: 0;
  font-size: 13.5px;
  color: var(--mut);
}
.es-desc {
  margin: 0;
  font-size: 12.5px;
  color: var(--dim);
}
</style>
