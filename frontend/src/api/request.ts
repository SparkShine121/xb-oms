import axios from 'axios'
import { ElMessage } from 'element-plus'
import { useUserStore } from '../stores/user'

const request = axios.create({ baseURL: '/api', timeout: 15000 })

request.interceptors.request.use(cfg => {
  const u = useUserStore()
  if (u.token) cfg.headers.Authorization = `Bearer ${u.token}`
  return cfg
})

request.interceptors.response.use(
  res => res.data,
  err => {
    if (err.response?.status === 401) {
      useUserStore().logout()
      // 已在登录页的 401（登录失败）交由 Login.vue 提示，不做整页跳转，避免刷新冲掉 toast
      if (location.pathname !== '/login') location.href = '/login'
    } else if (err.response) ElMessage.error(err.response.data?.message || '请求失败')
    return Promise.reject(err)
  }
)
export default request
