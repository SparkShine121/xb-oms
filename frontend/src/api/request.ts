import axios from 'axios'
import { ElMessage } from 'element-plus'
import { useUserStore } from '../stores/user'

const request = axios.create({ baseURL: '/api', timeout: 15000 })

request.interceptors.request.use(cfg => {
  const u = useUserStore()
  if (u.token) cfg.headers.Authorization = `Bearer ${u.token}`
  return cfg
})

// BUG-SIM-019 followup：refresh 自动续命——access 30min 到期时用 refreshToken 静默换新
// access 并重放原请求；refresh 也失效（过期/被 blacklist）才真正登出踢回登录页。
// 登录接口本身与 /auth/refresh/ 不参与续期（否则死循环）。
let refreshing: Promise<string | null> | null = null
const NO_REFRESH_URLS = ['/auth/login/', '/auth/refresh/', '/auth/logout/']

async function tryRefresh(): Promise<string | null> {
  const u = useUserStore()
  if (!u.refreshToken) return null
  if (!refreshing) {
    refreshing = axios
      .post('/api/auth/refresh/', { refresh: u.refreshToken }, { timeout: 15000 })
      .then(res => {
        const access: string = res.data?.data?.access
        if (access) u.setToken(access)
        return access ?? null
      })
      .catch(() => null)
      .finally(() => { refreshing = null })
  }
  return refreshing
}

request.interceptors.response.use(
  res => res.data,
  async err => {
    const u = useUserStore()
    const cfg = err.config
    const url: string = cfg?.url ?? ''
    const is401 = err.response?.status === 401
    const canRetry = is401 && cfg && !cfg._retried && !NO_REFRESH_URLS.some(p => url.includes(p))
    if (canRetry) {
      const access = await tryRefresh()
      if (access) {
        cfg._retried = true
        cfg.headers.Authorization = `Bearer ${access}`
        return request(cfg)
      }
    }
    if (is401) {
      await u.logout()
      // 已在登录页的 401（登录失败）交由 Login.vue 提示，不做整页跳转，避免刷新冲掉 toast
      if (location.pathname !== '/login') location.href = '/login'
    } else if (err.response) ElMessage({ type: 'error', message: err.response.data?.message || '请求失败', grouping: true })
    return Promise.reject(err)
  }
)
export default request
