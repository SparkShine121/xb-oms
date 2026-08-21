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
  return []
})

function onLogout() {
  userStore.logout()
  router.push('/login')
}
</script>

<template>
  <el-container class="main-layout">
    <el-aside width="220px">
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
        <el-sub-menu index="/system">
          <template #title>系统管理</template>
          <el-menu-item index="/system/users">用户管理</el-menu-item>
        </el-sub-menu>
        <el-sub-menu index="/orders">
          <template #title>订单管理</template>
          <el-menu-item index="/orders/list">订单列表</el-menu-item>
        </el-sub-menu>
        <el-sub-menu index="/tracking">
          <template #title>跟单管理</template>
          <el-menu-item index="/tracking">跟单工作台</el-menu-item>
        </el-sub-menu>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="layout-header">
        <div />
        <div class="header-user">
          <el-tag v-if="userStore.username" size="small">{{ userStore.username }}</el-tag>
          <el-button link type="primary" @click="onLogout">退出登录</el-button>
        </div>
      </el-header>
      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.main-layout {
  min-height: 100vh;
}
.logo {
  height: 60px;
  line-height: 60px;
  text-align: center;
  color: #fff;
  font-size: 16px;
  font-weight: 600;
  background: #1f3b73;
}
.layout-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #e4e7ed;
  background: #fff;
}
.header-user {
  display: flex;
  align-items: center;
  gap: 12px;
}
</style>
