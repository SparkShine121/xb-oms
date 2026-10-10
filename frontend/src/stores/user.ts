import { defineStore } from 'pinia'
import request from '../api/request'

export const useUserStore = defineStore('user', {
  state: () => ({
    token: sessionStorage.getItem('token') || '',
    refreshToken: sessionStorage.getItem('refreshToken') || '',
    id: Number(sessionStorage.getItem('userId')) || null as number | null,
    roles: JSON.parse(sessionStorage.getItem('roles') || '[]') as string[],
    username: sessionStorage.getItem('username') || '',
  }),
  actions: {
    setToken(t: string) { this.token = t; sessionStorage.setItem('token', t) },
    setRefreshToken(t: string) { this.refreshToken = t; sessionStorage.setItem('refreshToken', t) },
    setProfile(p: { id: number; username: string; roles: string[] }) {
      this.id = p.id
      this.username = p.username
      this.roles = p.roles
      sessionStorage.setItem('userId', String(p.id))
      sessionStorage.setItem('username', p.username)
      sessionStorage.setItem('roles', JSON.stringify(p.roles))
    },
    async logout() {
      // BUG-SIM-019/N7：退出真正调后端 logout（blacklist refresh）
      // 先取凭证再清空本地（防重入：401 拦截器在 await 期间再调 logout 时已无 token 直接跳过）
      const { token, refreshToken } = this
      this.token = ''; this.refreshToken = ''; this.id = null; this.roles = []; this.username = ''
      sessionStorage.removeItem('token')
      sessionStorage.removeItem('refreshToken')
      sessionStorage.removeItem('userId')
      sessionStorage.removeItem('username')
      sessionStorage.removeItem('roles')
      if (token && refreshToken) {
        try {
          await request.post('/auth/logout/', { refresh: refreshToken })
        } catch { /* 网络/401 异常不阻塞本地登出 */ }
      }
    },
  },
})
