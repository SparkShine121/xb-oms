<script setup lang="ts">
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '../stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

function onLogout() {
  userStore.logout()
  router.push('/login')
}
</script>

<template>
  <el-container class="main-layout">
    <el-aside width="220px">
      <div class="logo">辛巴印刷品定制</div>
      <el-menu :default-active="route.path" router>
        <el-menu-item index="/basic_info">基础信息</el-menu-item>
        <el-menu-item index="/system/users">用户管理</el-menu-item>
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
