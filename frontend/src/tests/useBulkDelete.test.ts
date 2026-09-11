// @vitest-environment node
// 纯逻辑测试不需要 DOM；mock element-plus（node 环境导入过慢，同既有测试惯例）
import { beforeEach, describe, expect, test, vi } from 'vitest'

const msgMock = vi.hoisted(() => ({ success: vi.fn(), warning: vi.fn(), error: vi.fn() }))
vi.mock('element-plus', () => ({
  ElMessage: msgMock,
  ElMessageBox: { confirm: vi.fn().mockResolvedValue(undefined) },
}))

import { useBulkDelete } from '../composables/useBulkDelete'

describe('useBulkDelete 提示按响应实际结果', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  test('全部删除成功 → success 提示', async () => {
    const deleter = vi.fn().mockResolvedValue({ code: 0, data: { deleted: 2, forbidden: [], not_found: [] } })
    const reload = vi.fn()
    const { handleSelectionChange, handleBatchDelete } = useBulkDelete(deleter, reload)
    handleSelectionChange([{ id: 1 }, { id: 2 }])
    await handleBatchDelete()
    expect(deleter).toHaveBeenCalledWith([1, 2])
    expect(msgMock.success).toHaveBeenCalledWith('已删除 2 条')
    expect(reload).toHaveBeenCalled()
  })

  test('部分无权限/不存在 → warning 列明各类数量', async () => {
    const deleter = vi.fn().mockResolvedValue({ code: 0, data: { deleted: 1, forbidden: [2], not_found: [3] } })
    const { handleSelectionChange, handleBatchDelete } = useBulkDelete(deleter, vi.fn())
    handleSelectionChange([{ id: 1 }, { id: 2 }, { id: 3 }])
    await handleBatchDelete()
    expect(msgMock.warning).toHaveBeenCalledWith('已删除 1 条，1 条无权限，1 条不存在')
    expect(msgMock.success).not.toHaveBeenCalled()
  })
})
