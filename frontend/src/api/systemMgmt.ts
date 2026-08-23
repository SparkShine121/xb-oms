import request from './request'
const base = '/system-mgmt'

// ---- 审批 ----
export const listApprovals = (p?: any) => request.get(`${base}/approvals/`, { params: p })
export const approveRequest = (id: number) => request.post(`${base}/approvals/${id}/approve/`)
export const rejectRequest = (id: number, note?: string) =>
  request.post(`${base}/approvals/${id}/reject/`, { note })

// ---- 操作日志 ----
export const listLogs = (p?: any) => request.get(`${base}/logs/`, { params: p })

// ---- 备份 ----
export const listBackups = (p?: any) => request.get(`${base}/backups/`, { params: p })
export const manualBackup = () => request.post(`${base}/backups/manual-backup/`)
// 下载走 blob（axios 层不做 envelope 解包，直接拿文件流）
export const downloadBackup = (id: number) =>
  request.get(`${base}/backups/${id}/download/`, { responseType: 'blob' })
