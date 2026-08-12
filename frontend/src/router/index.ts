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
      // Task 13: 基础信息模块页面
      { path: 'basic_info', redirect: '/basic-info/category' },
      {
        path: 'basic-info',
        redirect: '/basic-info/category',
        children: [
          { path: 'category', name: 'CategoryManage', component: () => import('../views/basic_info/CategoryManage.vue') },
          { path: 'product', name: 'ProductManage', component: () => import('../views/basic_info/ProductManage.vue') },
          { path: 'factory', name: 'FactoryManage', component: () => import('../views/basic_info/FactoryManage.vue') },
          { path: 'logistics', name: 'LogisticsManage', component: () => import('../views/basic_info/LogisticsManage.vue') },
          { path: 'customer', name: 'CustomerManage', component: () => import('../views/basic_info/CustomerManage.vue') },
        ],
      },
      // Task 14: 系统管理 - 用户管理
      { path: 'system/users', name: 'UserManage', component: () => import('../views/system/UserManage.vue') },
    ],
  },
  {
    path: '/m',
    component: MobileLayout,
    children: [
      // Task 15: 移动端只读浏览（Vant）
      { path: '', name: 'MobileHome', component: () => import('../views/m/MobileHome.vue') },
      { path: 'products', name: 'MProductList', component: () => import('../views/m/MProductList.vue') },
      { path: 'factories', name: 'MFactoryList', component: () => import('../views/m/MFactoryList.vue') },
      { path: 'customers', name: 'MCustomerList', component: () => import('../views/m/MCustomerList.vue') },
      // 我的：占位，后续任务实现
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
