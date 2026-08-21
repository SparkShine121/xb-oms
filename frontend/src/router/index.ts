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
      // 订单管理：OT8 PC 列表 + 详情；OT9 PC 表单（new/edit）
      { path: 'orders', redirect: '/orders/list' },
      { path: 'orders/list', name: 'OrderList', component: () => import('../views/orders/OrderList.vue') },
      { path: 'orders/new', name: 'OrderNew', component: () => import('../views/orders/OrderForm.vue') },
      { path: 'orders/:id', name: 'OrderDetail', component: () => import('../views/orders/OrderDetail.vue') },
      { path: 'orders/:id/edit', name: 'OrderEdit', component: () => import('../views/orders/OrderForm.vue'), props: true },
      // 跟单管理：TT5 实现 TrackingWorkbench
      { path: 'tracking', name: 'TrackingWorkbench', component: () => import('../views/tracking/TrackingWorkbench.vue') },
      // 工厂结算：FT5 列表+详情，FT6 对账单
      { path: 'factory-payment', name: 'FactoryPayment', component: () => import('../views/factory_payment/FactoryPaymentList.vue') },
      { path: 'factory-payment/:id', name: 'FactoryPaymentDetail', component: () => import('../views/factory_payment/FactoryPaymentDetail.vue') },
      { path: 'factory-payment/statement', name: 'FactoryPaymentStatement', component: Placeholder },
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
      // 订单管理（移动端）：OT10 列表 + 详情；OT11 表单（new/edit）
      { path: 'orders', name: 'MOrderList', component: () => import('../views/m/orders/MOrderList.vue') },
      { path: 'orders/new', name: 'MOrderNew', component: () => import('../views/m/orders/MOrderForm.vue') },
      { path: 'orders/:id', name: 'MOrderDetail', component: () => import('../views/m/orders/MOrderDetail.vue') },
      { path: 'orders/:id/edit', name: 'MOrderEdit', component: () => import('../views/m/orders/MOrderForm.vue'), props: true },
      // 跟单（移动端）：TT6 实现 MTrackingWorkbench
      { path: 'tracking', name: 'MTrackingWorkbench', component: () => import('../views/m/tracking/MTrackingWorkbench.vue') },
      // 工厂结算（移动端）：FT4 占位，Task 7 替换
      { path: 'factory-payment', name: 'MFactoryPayment', component: Placeholder },
      { path: 'factory-payment/statement', name: 'MFactoryPaymentStatement', component: Placeholder },
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
