// @vitest-environment node
import { vi } from 'vitest'
vi.mock('element-plus', () => ({ ElMessage: { error: () => {} } }))

const http = vi.hoisted(() => ({
  get: vi.fn((_url: string, _cfg: any = {}) => Promise.resolve({ data: {} })),
  post: vi.fn((_url: string, _body?: any) => Promise.resolve({ data: {} })),
  patch: vi.fn((_url: string, _body?: any) => Promise.resolve({ data: {} })),
  delete: vi.fn((_url: string) => Promise.resolve({ data: {} })),
}))
vi.mock('../api/request', () => ({ default: http }))

import * as finance from '../api/finance'

test('finance api exports', async () => {
  expect(typeof finance.listPaymentsIn).toBe('function')
  expect(typeof finance.getPaymentIn).toBe('function')
  expect(typeof finance.createPaymentIn).toBe('function')
  expect(typeof finance.deletePaymentIn).toBe('function')
  expect(typeof finance.listLedger).toBe('function')
  expect(typeof finance.exportLedger).toBe('function')
})

test('finance api hits expected endpoints', async () => {
  await finance.listPaymentsIn({ page: 1 })
  const [url1, cfg1] = http.get.mock.calls.at(-1)!
  expect(url1).toBe('/finance/payments-in/')
  expect(cfg1.params.page).toBe(1)

  await finance.getPaymentIn(7)
  expect(http.get.mock.calls.at(-1)![0]).toBe('/finance/payments-in/7/')

  await finance.createPaymentIn({ order: 1 })
  expect(http.post.mock.calls.at(-1)![0]).toBe('/finance/payments-in/')

  await finance.deletePaymentIn(7)
  expect(http.delete.mock.calls.at(-1)![0]).toBe('/finance/payments-in/7/')

  await finance.listLedger({ start_date: '2026-08-01', type: 'income_receipt' })
  const [url2, cfg2] = http.get.mock.calls.at(-1)!
  expect(url2).toBe('/finance/payments-in/ledger/')
  expect(cfg2.params.start_date).toBe('2026-08-01')
  expect(cfg2.params.type).toBe('income_receipt')

  await finance.exportLedger({ end_date: '2026-08-31' })
  const [url3, cfg3] = http.get.mock.calls.at(-1)!
  expect(url3).toBe('/finance/payments-in/export/')
  expect(cfg3.responseType).toBe('blob')
  expect(cfg3.params.end_date).toBe('2026-08-31')
})
