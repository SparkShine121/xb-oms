import { defineStore } from 'pinia'

export const useUserStore = defineStore('user', {
  state: () => ({
    token: sessionStorage.getItem('token') || '',
    roles: JSON.parse(sessionStorage.getItem('roles') || '[]') as string[],
    username: sessionStorage.getItem('username') || '',
  }),
  actions: {
    setToken(t: string) { this.token = t; sessionStorage.setItem('token', t) },
    setProfile(p: { username: string; roles: string[] }) {
      this.username = p.username
      this.roles = p.roles
      sessionStorage.setItem('username', p.username)
      sessionStorage.setItem('roles', JSON.stringify(p.roles))
    },
    logout() {
      this.token = ''; this.roles = []; this.username = ''
      sessionStorage.removeItem('token')
      sessionStorage.removeItem('username')
      sessionStorage.removeItem('roles')
    },
  },
})
