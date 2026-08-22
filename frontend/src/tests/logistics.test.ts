// @vitest-environment node
import { vi } from 'vitest'
vi.mock('element-plus', () => ({ ElMessage: { error: () => {} } }))

test('logistics api exports', async () => {
  const m = await import('../api/logistics')
  expect(typeof m.listShipments).toBe('function')
  expect(typeof m.getShipment).toBe('function')
  expect(typeof m.createShipment).toBe('function')
  expect(typeof m.updateShipment).toBe('function')
  expect(typeof m.deleteShipment).toBe('function')
})
