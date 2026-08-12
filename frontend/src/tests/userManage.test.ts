// @vitest-environment node
// 纯逻辑测试不需要 DOM；jsdom 在此 ARM 平板环境初始化过慢（>60s 超时）。
// request.ts 引用了 element-plus 的 ElMessage（全局错误提示），node 环境导入 element-plus 过慢会超时，mock 掉
vi.mock('element-plus', () => ({ ElMessage: { error: vi.fn() } }))
// 仅验证导出函数存在与签名（不调网络）
test('user admin api exports', async () => {
  const m = await import('../api/auth')
  expect(typeof m.listUsers).toBe('function')
  expect(typeof m.createUser).toBe('function')
  expect(typeof m.deleteUser).toBe('function')
})
