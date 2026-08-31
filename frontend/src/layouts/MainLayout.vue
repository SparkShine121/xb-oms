<script setup lang="ts">
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '../stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

// 根据当前路由自动展开对应子菜单
const defaultOpeneds = computed(() => {
  if (route.path.startsWith('/basic-info')) return ['/basic-info']
  if (route.path.startsWith('/system')) return ['/system']
  if (route.path.startsWith('/orders')) return ['/orders']
  if (route.path.startsWith('/tracking')) return ['/tracking']
  if (route.path.startsWith('/factory-payment')) return ['/factory-payment']
  if (route.path.startsWith('/logistics')) return ['/logistics']
  if (route.path.startsWith('/finance')) return ['/finance']
  return []
})

function onLogout() {
  userStore.logout()
  router.push('/login')
}

// 系统管理仅 admin 可见
const isAdmin = computed(() => userStore.roles.includes('admin'))
</script>

<template>
  <el-container class="main-layout">
    <el-aside width="220px" class="layout-aside">
      <div class="logo">xbb印刷品定制</div>
      <el-menu :default-active="route.path" :default-openeds="defaultOpeneds" router>
        <el-sub-menu index="/basic-info">
          <template #title>基础信息</template>
          <el-menu-item index="/basic-info/category">类目</el-menu-item>
          <el-menu-item index="/basic-info/product">产品库</el-menu-item>
          <el-menu-item index="/basic-info/factory">工厂库</el-menu-item>
          <el-menu-item index="/basic-info/logistics">物流服务商</el-menu-item>
          <el-menu-item index="/basic-info/customer">客户</el-menu-item>
        </el-sub-menu>
        <el-sub-menu v-if="isAdmin" index="/system">
          <template #title>系统管理</template>
          <el-menu-item index="/system/approvals">待审批</el-menu-item>
          <el-menu-item index="/system/users">用户管理</el-menu-item>
          <el-menu-item index="/system/logs">操作日志</el-menu-item>
          <el-menu-item index="/system/backups">备份管理</el-menu-item>
        </el-sub-menu>
        <el-sub-menu index="/orders">
          <template #title>订单管理</template>
          <el-menu-item index="/orders/list">订单列表</el-menu-item>
        </el-sub-menu>
        <el-sub-menu index="/tracking">
          <template #title>跟单管理</template>
          <el-menu-item index="/tracking">跟单工作台</el-menu-item>
        </el-sub-menu>
        <el-sub-menu index="/factory-payment">
          <template #title>工厂结算</template>
          <el-menu-item index="/factory-payment">结算单</el-menu-item>
          <el-menu-item index="/factory-payment/statement">对账单</el-menu-item>
        </el-sub-menu>
        <el-sub-menu index="/logistics">
          <template #title>物流管理</template>
          <el-menu-item index="/logistics">发货单</el-menu-item>
        </el-sub-menu>
        <el-sub-menu index="/finance">
          <template #title>轻财务</template>
          <el-menu-item index="/finance">收支流水</el-menu-item>
        </el-sub-menu>
        <el-menu-item index="/analytics">数据分析</el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="layout-header">
        <div class="header-crumb">管理系统</div>
        <div class="header-user">
          <el-tag v-if="userStore.username" size="small" effect="light">{{ userStore.username }}</el-tag>
          <el-button link type="primary" @click="onLogout">退出登录</el-button>
        </div>
      </el-header>
      <el-main class="layout-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.main-layout {
  min-height: 100vh;
  background: var(--bg-page);
}
.layout-aside {
  display: flex;
  flex-direction: column;
  background: var(--surface);
  border-right: 1px solid var(--border);
}
.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 16px;
  font-weight: 700;
  letter-spacing: 1px;
  background: linear-gradient(135deg, var(--brand-800), var(--brand-600));
}
.layout-aside .el-menu {
  flex: 1;
  padding: 8px 0;
}
.layout-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 56px;
  border-bottom: 1px solid var(--border);
  background: var(--surface);
  padding: 0 20px;
}
.header-crumb {
  color: var(--text-700);
  font-weight: 600;
}
.header-user {
  display: flex;
  align-items: center;
  gap: 12px;
}
.layout-main {
  padding: 20px;
  background: var(--bg-page);
}
</style>
