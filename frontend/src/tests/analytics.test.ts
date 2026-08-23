// @vitest-environment node
import { vi } from 'vitest'
vi.mock('element-plus', () => ({ ElMessage: { error: () => {} } }))

test('analytics api exports', async () => {
  const m = await import('../api/analytics')
  expect(typeof m.getSalesSummary).toBe('function')
  expect(typeof m.getFactorySummary).toBe('function')
  expect(typeof m.getTrackingSummary).toBe('function')
  expect(typeof m.getOverview).toBe('function')
})
