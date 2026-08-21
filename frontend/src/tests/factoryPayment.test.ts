// @vitest-environment node
import { vi } from 'vitest'
vi.mock('element-plus', () => ({ ElMessage: { error: () => {} } }))
beforeEach(() => vi.resetModules())

test('factoryPayment api exports', async () => {
  const m = await import('../api/factoryPayment')
  expect(typeof m.listPayments).toBe('function')
  expect(typeof m.createPayment).toBe('function')
  expect(typeof m.createRecord).toBe('function')
  expect(typeof m.generateByOrder).toBe('function')
  expect(typeof m.getStatement).toBe('function')
})
