import { ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

/**
 * 表格多选 + 批量删除（配合 el-table 的 type="selection" 列使用）。
 * @param deleter 批量删除 API，接收 id 数组，返回 Promise
 * @param reload  删除成功后的刷新函数（如 load()）
 */
export function useBulkDelete(deleter: (ids: number[]) => Promise<any>, reload: () => void) {
  const selection = ref<any[]>([])

  function handleSelectionChange(val: any[]) {
    selection.value = val
  }

  async function handleBatchDelete() {
    if (!selection.value.length) return ElMessage.warning('请先勾选要删除的记录')
    const count = selection.value.length
    await ElMessageBox.confirm(`确定删除选中的 ${count} 条记录？`, '批量删除', { type: 'warning' })
    // 后端响应 data: {deleted, forbidden, not_found}（BUG-SIM-001 修复后新增清单）
    const resp = await deleter(selection.value.map((r: any) => r.id))
    const { deleted = count, forbidden = [], not_found = [] } = resp?.data ?? {}
    if (forbidden.length || not_found.length) {
      ElMessage.warning(
        `已删除 ${deleted} 条` +
        (forbidden.length ? `，${forbidden.length} 条无权限` : '') +
        (not_found.length ? `，${not_found.length} 条不存在` : '')
      )
    } else {
      ElMessage.success(`已删除 ${deleted} 条`)
    }
    reload()
  }

  return { selection, handleSelectionChange, handleBatchDelete }
}
