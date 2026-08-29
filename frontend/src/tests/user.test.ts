// @vitest-environment node
// 纯逻辑测试不需要 DOM；jsdom 在此 ARM 平板环境初始化过慢（>60s 超时）。
import { setActivePinia, createPinia } from 'pinia'
import { useUserStore } from '../stores/user'

beforeEach(() => { setActivePinia(createPinia()); sessionStorage.clear() })

test('setToken stores token', () => {
  const s = useUserStore()
  s.setToken('abc')
  expect(s.token).toBe('abc')
  expect(sessionStorage.getItem('token')).toBe('abc')
})

test('logout clears token and roles', () => {
  const s = useUserStore()
  s.setToken('abc'); s.roles = ['admin']
  s.logout()
  expect(s.token).toBe(''); expect(s.roles).toEqual([])
})
