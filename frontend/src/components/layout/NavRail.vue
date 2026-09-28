<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { MENU_GROUPS, groupOfPath } from '../../layouts/menuConfig'
import { useUserStore } from '../../stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const isAdmin = computed(() => userStore.roles.includes('admin'))
const visibleGroups = computed(() => MENU_GROUPS.filter((g) => !g.adminOnly || isAdmin.value))

/** 当前路由所属分组（rail 激活态） */
const activeKey = computed(() => groupOfPath(route.path)?.key ?? '')

/** flyout 展开/悬停的分组；单页分组无 flyout */
const openKey = ref<string | null>(null)
let hoverTimer: ReturnType<typeof setTimeout> | null = null

/** Q1-a：children 为 0 或 1 的分组点击直达目标页；多页分组点击切换 flyout */
function toggleOrGo(key: string) {
  const g = MENU_GROUPS.find((x) => x.key === key)!
  if (g.children.length <= 1) return go(g)
  if (openKey.value === key) return closeFlyout()
  openKey.value = key
}

function closeFlyout() {
  openKey.value = null
}

/** hover 120ms 延迟预览：仅对多页分组生效（单页分组 hover 不弹） */
function hoverOpen(key: string) {
  const g = MENU_GROUPS.find((x) => x.key === key)!
  if (!g.children.length || g.children.length === 1) return
  if (hoverTimer) clearTimeout(hoverTimer)
  hoverTimer = setTimeout(() => { openKey.value = key }, 120)
}

function hoverLeave() {
  if (hoverTimer) clearTimeout(hoverTimer)
}

function go(g: (typeof MENU_GROUPS)[number]) {
  openKey.value = null
  const target = g.children.length ? g.children[0].path : g.path
  if (target && route.path !== target) router.push(target)
}

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') openKey.value = null
}
function onDocClick(e: MouseEvent) {
  if (!(e.target as HTMLElement).closest('.nav-rail')) openKey.value = null
}
onMounted(() => { document.addEventListener('click', onDocClick) })
onBeforeUnmount(() => { document.removeEventListener('click', onDocClick) })

const userInitial = computed(() => (userStore.username || '?').slice(0, 1).toUpperCase())
const userPop = ref(false)
function toggleUserPop() { userPop.value = !userPop.value }
function onLogout() {
  userPop.value = false
  userStore.logout()
  router.push('/login')
}
</script>

<template>
  <nav class="nav-rail" @keydown="onKeydown">
    <div class="rail-logo" title="xbb 印刷品定制">印</div>

    <button
      v-for="g in visibleGroups"
      :key="g.key"
      type="button"
      class="rail-item"
      :class="{ on: activeKey === g.key }"
      :aria-label="g.label"
      @click="toggleOrGo(g.key)"
      @mouseenter="hoverOpen(g.key)"
      @mouseleave="hoverLeave"
    >
      <component :is="g.icon" :size="20" weight="regular" />
      <span class="rail-label">{{ g.label }}</span>
      <div v-if="openKey === g.key && g.children.length > 1" class="rail-flyout" @click.stop>
        <p class="flyout-title">{{ g.label }}</p>
        <router-link
          v-for="c in g.children"
          :key="c.path"
          :to="c.path"
          class="flyout-item"
          :class="{ on: route.path === c.path }"
          @click="openKey = null"
        >
          {{ c.label }}
        </router-link>
      </div>
    </button>

    <div class="rail-spacer" />

    <!-- 底部用户入口：独立类名 .rail-user（不占导航项计数），样式与 .rail-item 共享 -->
    <button type="button" class="rail-user" aria-label="用户" @click="toggleUserPop">
      <span class="user-avatar">{{ userInitial }}</span>
      <span class="rail-label">我的</span>
      <div v-if="userPop" class="user-pop" @click.stop>
        <p class="user-pop-name">{{ userStore.username }}</p>
        <p class="user-pop-roles">{{ userStore.roles.join(' / ') }}</p>
        <button type="button" class="user-pop-logout" @click="onLogout">退出登录</button>
      </div>
    </button>
  </nav>
</template>

<style scoped>
.nav-rail {
  width: 76px;
  flex: none;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 16px 0;
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: var(--r-frame);
  position: relative;
}
.rail-logo {
  width: 38px;
  height: 38px;
  border-radius: var(--r-ctl);
  background: var(--lime);
  color: var(--lime-ink);
  font-weight: 700;
  font-size: 17px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 14px;
  flex: none;
}
.rail-item,
.rail-user {
  position: relative;
  width: 48px;
  height: 46px;
  border-radius: var(--r-nav);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1px;
  color: var(--mut);
  background: transparent;
  border: none;
  cursor: pointer;
  transition: background 0.22s var(--ease), color 0.22s var(--ease);
}
.rail-item:hover,
.rail-user:hover { background: var(--panel2); color: var(--txt); }
.rail-item.on { background: var(--panel3); color: var(--lime-deep); }
.rail-label {
  font-size: 10.5px;
  line-height: 1.2;
  white-space: nowrap;
}
.rail-spacer { flex: 1; }
.rail-user { margin-top: 8px; }
.user-avatar {
  width: 26px;
  height: 26px;
  border-radius: 8px;
  background: var(--panel3);
  color: var(--txt);
  font-size: 12px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
}
/* flyout：rail 右侧浮出 */
.rail-flyout {
  position: absolute;
  left: 60px;
  top: 50%;
  transform: translateY(-50%);
  width: 200px;
  background: var(--panel);
  border: 1px solid var(--line2);
  border-radius: var(--r-card);
  box-shadow: var(--shadow-pop);
  padding: 10px;
  z-index: 60;
  text-align: left;
}
.flyout-title {
  margin: 2px 8px 8px;
  font-size: 11px;
  color: var(--dim);
  letter-spacing: 0.08em;
}
.flyout-item {
  display: block;
  padding: 8px 10px;
  border-radius: var(--r-sm);
  font-size: 13px;
  color: var(--mut);
  text-decoration: none;
  transition: background 0.15s var(--ease), color 0.15s var(--ease);
}
.flyout-item:hover { background: var(--panel2); color: var(--txt); }
.flyout-item.on { background: var(--panel3); color: var(--lime-deep); font-weight: 500; }
/* 用户弹出菜单 */
.user-pop {
  position: absolute;
  left: 60px;
  bottom: 0;
  width: 200px;
  background: var(--panel);
  border: 1px solid var(--line2);
  border-radius: var(--r-card);
  box-shadow: var(--shadow-pop);
  padding: 14px;
  z-index: 60;
  text-align: left;
}
.user-pop-name { margin: 0; font-size: 14px; font-weight: 600; color: var(--txt); }
.user-pop-roles { margin: 4px 0 10px; font-size: 11.5px; color: var(--dim); }
.user-pop-logout {
  width: 100%;
  padding: 8px;
  border-radius: var(--r-sm);
  border: 1px solid var(--line2);
  background: var(--panel2);
  color: var(--danger);
  font-size: 13px;
  cursor: pointer;
}
</style>
