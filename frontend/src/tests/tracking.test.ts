// @vitest-environment node
import { vi } from 'vitest'
vi.mock('element-plus', () => ({ ElMessage: { error: () => {} } }))
test('tracking api exports', async () => {
  const m = await import('../api/tracking')
  expect(typeof m.listMyOrders).toBe('function')
  expect(typeof m.advanceOrder).toBe('function')
  expect(typeof m.rejectOrder).toBe('function')
  expect(typeof m.getTimeline).toBe('function')
})
