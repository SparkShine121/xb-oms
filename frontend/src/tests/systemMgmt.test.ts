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

import * as systemMgmt from '../api/systemMgmt'

test('system mgmt api exports', async () => {
  expect(typeof systemMgmt.listApprovals).toBe('function')
  expect(typeof systemMgmt.approveRequest).toBe('function')
  expect(typeof systemMgmt.rejectRequest).toBe('function')
  expect(typeof systemMgmt.listLogs).toBe('function')
  expect(typeof systemMgmt.listBackups).toBe('function')
  expect(typeof systemMgmt.manualBackup).toBe('function')
  expect(typeof systemMgmt.downloadBackup).toBe('function')
})

test('approvals api hits expected endpoints', async () => {
  await systemMgmt.listApprovals({ page: 1, status: 'pending' })
  const [url0, cfg0] = http.get.mock.calls.at(-1)!
  expect(url0).toBe('/system-mgmt/approvals/')
  expect(cfg0.params.page).toBe(1)
  expect(cfg0.params.status).toBe('pending')

  await systemMgmt.approveRequest(7)
  const [url1] = http.post.mock.calls.at(-1)!
  expect(url1).toBe('/system-mgmt/approvals/7/approve/')

  await systemMgmt.rejectRequest(8, '金额有误')
  const [url2, body2] = http.post.mock.calls.at(-1)!
  expect(url2).toBe('/system-mgmt/approvals/8/reject/')
  expect(body2.note).toBe('金额有误')
})

test('logs api hits expected endpoints', async () => {
  await systemMgmt.listLogs({ action: 'POST', page: 2 })
  const [url, cfg] = http.get.mock.calls.at(-1)!
  expect(url).toBe('/system-mgmt/logs/')
  expect(cfg.params.action).toBe('POST')
  expect(cfg.params.page).toBe(2)
})

test('backup api hits expected endpoints', async () => {
  await systemMgmt.listBackups({ page: 1 })
  const [url0, cfg0] = http.get.mock.calls.at(-1)!
  expect(url0).toBe('/system-mgmt/backups/')
  expect(cfg0.params.page).toBe(1)

  await systemMgmt.manualBackup()
  const [url1] = http.post.mock.calls.at(-1)!
  expect(url1).toBe('/system-mgmt/backups/manual-backup/')

  await systemMgmt.downloadBackup(9)
  const [url2, cfg2] = http.get.mock.calls.at(-1)!
  expect(url2).toBe('/system-mgmt/backups/9/download/')
  expect(cfg2.responseType).toBe('blob')
})
