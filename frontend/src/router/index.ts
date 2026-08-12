import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '../stores/user'
import MainLayout from '../layouts/MainLayout.vue'
import MobileLayout from '../layouts/MobileLayout.vue'
import Placeholder from '../views/Placeholder.vue'

const routes = [
  { path: '/login', name: 'Login', component: () => import('../views/Login.vue') },
  {
    path: '/',
    component: MainLayout,
    redirect: '/basic_info',
    children: [
      // Task 13: 基础信息模块页面（客户/商品/材料/供应商等），届时替换 Placeholder
      { path: 'basic_info', component: Placeholder },
      // Task 14: 系统管理 - 用户管理
      { path: 'system/users', component: Placeholder },
    ],
  },
  {
    path: '/m',
    component: MobileLayout,
    redirect: '/m/home',
    children: [
      // 移动端子路由占位，具体页面后续任务实现
      { path: 'home', component: Placeholder },
      { path: 'quote', component: Placeholder },
      { path: 'me', component: Placeholder },
    ],
  },
  { path: '/:pathMatch(.*)*', redirect: '/login' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(to => {
  const u = useUserStore()
  if (!u.token && to.path !== '/login') return '/login'
  if (u.token && to.path === '/login') return '/'
})

export default router
