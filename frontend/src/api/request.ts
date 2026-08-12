import axios from 'axios'
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
    if (err.response?.status === 401) { useUserStore().logout(); location.href = '/login' }
    return Promise.reject(err)
  }
)
export default request
