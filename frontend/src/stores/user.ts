import { defineStore } from 'pinia'

export const useUserStore = defineStore('user', {
  state: () => ({ token: sessionStorage.getItem('token') || '', roles: [] as string[], username: '' }),
  actions: {
    setToken(t: string) { this.token = t; sessionStorage.setItem('token', t) },
    setProfile(p: { username: string; roles: string[] }) { this.username = p.username; this.roles = p.roles },
    logout() { this.token = ''; this.roles = []; this.username = ''; sessionStorage.removeItem('token') },
  },
})
