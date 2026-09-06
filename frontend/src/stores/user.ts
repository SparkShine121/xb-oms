import { defineStore } from 'pinia'

export const useUserStore = defineStore('user', {
  state: () => ({
    token: sessionStorage.getItem('token') || '',
    id: Number(sessionStorage.getItem('userId')) || null as number | null,
    roles: JSON.parse(sessionStorage.getItem('roles') || '[]') as string[],
    username: sessionStorage.getItem('username') || '',
  }),
  actions: {
    setToken(t: string) { this.token = t; sessionStorage.setItem('token', t) },
    setProfile(p: { id: number; username: string; roles: string[] }) {
      this.id = p.id
      this.username = p.username
      this.roles = p.roles
      sessionStorage.setItem('userId', String(p.id))
      sessionStorage.setItem('username', p.username)
      sessionStorage.setItem('roles', JSON.stringify(p.roles))
    },
    logout() {
      this.token = ''; this.id = null; this.roles = []; this.username = ''
      sessionStorage.removeItem('token')
      sessionStorage.removeItem('userId')
      sessionStorage.removeItem('username')
      sessionStorage.removeItem('roles')
    },
  },
})
