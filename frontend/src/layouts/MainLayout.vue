<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import NavRail from '../components/layout/NavRail.vue'
import { groupOfPath } from './menuConfig'

const route = useRoute()
/** 面包屑只到分组级（Q3-a）：顶栏显示当前域，页头 h2 显示当前页面 */
const crumb = computed(() => groupOfPath(route.path)?.label ?? '')
</script>

<template>
  <div class="app-shell">
    <NavRail />
    <div class="main-column">
      <header class="topbar">
        <nav class="crumbs" aria-label="当前位置">{{ crumb }}</nav>
      </header>
      <main class="content-view">
        <router-view />
      </main>
    </div>
  </div>
</template>

<style scoped>
.app-shell {
  display: flex;
  gap: 12px;
  padding: 12px;
  height: 100dvh;
  background: var(--canvas);
}
.main-column {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.topbar {
  flex: none;
  display: flex;
  align-items: center;
  padding: 14px 22px;
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: var(--r-frame);
}
.crumbs {
  font-size: 14px;
  font-weight: 600;
  color: var(--txt);
}
.content-view {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 22px 24px;
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: var(--r-frame);
  scroll-behavior: smooth;
}
</style>
