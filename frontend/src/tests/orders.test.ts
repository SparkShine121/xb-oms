// @vitest-environment node
// 纯逻辑测试不需要 DOM；jsdom 在此 ARM 平板环境初始化过慢（>60s 超时）。
import { vi } from 'vitest'
vi.mock('element-plus', () => ({ ElMessage: { error: () => {} } }))
beforeEach(() => vi.resetModules())
test('orders api exports', async () => {
  const m = await import('../api/orders')
  expect(typeof m.listOrders).toBe('function')
  expect(typeof m.createOrder).toBe('function')
  expect(typeof m.importOrders).toBe('function')
  expect(typeof m.downloadOrderTemplate).toBe('function')
  expect(typeof m.setTracker).toBe('function')
  expect(typeof m.listExchangeRates).toBe('function')
})