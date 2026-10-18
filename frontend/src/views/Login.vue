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
    userStore.setRefreshToken(res.data.refresh) // BUG-SIM-019：供退出时 blacklist
    try {
      const info = await me()
      userStore.setProfile(info.data)
    } catch {
      // 获取用户信息失败不阻塞登录
    }
    // UX-低优#5：成功后清掉残留的失败提示（3s 窗口内旧错误对已登录用户无意义）
    ElMessage.closeAll()
    router.push('/')
  } catch (e: any) {
    const msg = typeof e.response?.data?.message === 'string' ? e.response?.data?.message : '登录失败'
    // grouping：连续失败相同内容合并为单条带计数，防堆叠
    ElMessage({ message: msg, type: 'error', customClass: 'login-toast', grouping: true })
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <div class="login-brand">
      <p class="lb-tag">xbb 印刷品定制 · 数字化管理</p>
      <h1 class="lb-title">把订单、工厂与跟单<br />装进一块屏幕。</h1>
      <p class="lb-sub">基础信息、订单、跟单、工厂结算与轻财务，一个入口全部收拢。</p>
      <div class="lb-ring lb-ring-a" aria-hidden="true" />
      <div class="lb-ring lb-ring-b" aria-hidden="true" />
    </div>
    <div class="login-side">
      <div class="login-card">
        <h2 class="login-title">登录工作台</h2>
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
              进入工作台 →
            </el-button>
          </el-form-item>
        </el-form>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  display: flex;
  min-height: 100dvh;
  background: var(--canvas);
  background-image: radial-gradient(720px 520px at 10% 8%, var(--lime-tint), transparent 58%),
    radial-gradient(640px 460px at 92% 94%, var(--lime-tint), transparent 60%);
}
.login-brand {
  flex: 1.1;
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 8vh 6vw;
}
.lb-tag {
  margin: 0;
  color: var(--lime-text);
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 0.12em;
}
.lb-tag::before {
  content: '';
  display: inline-block;
  width: 22px;
  height: 2px;
  background: var(--lime);
  margin-right: 8px;
  vertical-align: 4px;
}
.lb-title {
  margin: 22px 0 14px;
  font-size: clamp(34px, 4vw, 50px);
  font-weight: 700;
  letter-spacing: -0.02em;
  line-height: 1.22;
  color: var(--txt);
  max-width: 15em;
}
.lb-sub {
  margin: 0;
  max-width: 420px;
  color: var(--mut);
  font-size: 14px;
  line-height: 1.7;
}
.lb-ring {
  position: absolute;
  border-radius: 50%;
  pointer-events: none;
}
.lb-ring-a {
  width: 420px;
  height: 420px;
  border: 1px solid var(--line);
  right: -140px;
  top: -120px;
}
.lb-ring-b {
  width: 280px;
  height: 280px;
  border: 1px dashed var(--line2);
  left: 6%;
  bottom: -110px;
}
.login-side {
  flex: 0.9;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 24px;
}
.login-card {
  width: min(420px, 100%);
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: var(--r-frame);
  padding: 32px;
  box-shadow: var(--shadow-overlay);
}
.login-title {
  text-align: center;
  margin: 4px 0 28px;
  color: var(--txt);
  font-size: 20px;
  font-weight: 700;
}
.login-btn {
  width: 100%;
}
@media (max-width: 900px) {
  .login-brand { display: none; }
  .login-side { flex: 1; }
}
</style>
