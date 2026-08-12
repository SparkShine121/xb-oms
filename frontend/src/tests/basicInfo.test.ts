// @vitest-environment node
// 纯逻辑测试不需要 DOM；jsdom 在此 ARM 平板环境初始化过慢（>60s 超时）。
import { setActivePinia, createPinia } from 'pinia'
beforeEach(() => setActivePinia(createPinia()))
// 仅验证导出函数存在与签名（不调网络）
test('basicInfo api exports', async () => {
  const m = await import('../api/basicInfo')
  expect(typeof m.listCategories).toBe('function')
  expect(typeof m.importProducts).toBe('function')
  expect(typeof m.downloadProductTemplate).toBe('function')
})
