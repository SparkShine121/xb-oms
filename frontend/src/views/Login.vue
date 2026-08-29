<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '../stores/user'
import { login, me } from '../api/auth'

const router = useRouter()
const userStore = useUserStore()
const form = reactive({ username: '', password: '' })
const loading = ref(false)

async function onSubmit() {
  if (loading.value) return
  if (!form.username || !form.password) {
    ElMessage.warning('请输入用户名和密码')
    return
  }
  loading.value = true
  try {
    const res = await login(form)
    userStore.setToken(res.data.access)
    try {
      const info = await me()
      userStore.setProfile(info.data)
    } catch {
      // 获取用户信息失败不阻塞登录
    }
    router.push('/')
  } catch (e: any) {
    const msg = typeof e.response?.data?.message === 'string' ? e.response?.data?.message : '登录失败'
    ElMessage({ message: msg, type: 'error', customClass: 'login-toast' })
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <el-card class="login-card">
      <h2 class="login-title">xbb印刷品定制管理系统</h2>
      <el-form :model="form" label-width="0" @submit.prevent="onSubmit">
        <el-form-item>
          <el-input v-model="form.username" placeholder="用户名" size="large" autocomplete="username" />
        </el-form-item>
        <el-form-item>
          <el-input
            v-model="form.password"
            type="password"
            placeholder="密码"
            size="large"
            show-password
            autocomplete="current-password"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" size="large" class="login-btn" :loading="loading" native-type="submit">
            登 录
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<style scoped>
.login-page {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 100%);
}
.login-card {
  width: 380px;
  padding: 28px 24px;
  border-radius: var(--radius-lg);
  border: 1px solid rgba(255, 255, 255, 0.4);
  box-shadow: var(--shadow-pop);
}
.login-title {
  text-align: center;
  margin: 4px 0 28px;
  color: var(--brand-800);
  font-size: 20px;
  font-weight: 700;
}
.login-btn {
  width: 100%;
}
</style>

<style>
/* 登录失败的 toast 居中显示在页面中间 */
.login-toast.el-message {
  position: fixed !important;
  top: 50% !important;
  left: 50% !important;
  right: auto !important;
  bottom: auto !important;
  transform: translate(-50%, -50%) !important;
  margin: 0 !important;
}
</style>
