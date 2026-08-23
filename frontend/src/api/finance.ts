import request from './request'
const base = '/finance/payments-in'

export const listPaymentsIn = (p?: any) => request.get(`${base}/`, { params: p })
export const getPaymentIn = (id: number) => request.get(`${base}/${id}/`)
export const createPaymentIn = (d: any) => request.post(`${base}/`, d)
export const updatePaymentIn = (id: number, d: any) => request.patch(`${base}/${id}/`, d)
export const deletePaymentIn = (id: number) => request.delete(`${base}/${id}/`)
export const listLedger = (p?: any) => request.get(`${base}/ledger/`, { params: p })
// 导出走 blob（axios 层不做 envelope 解包，直接拿文件流）
export const exportLedger = (p?: any) =>
  request.get(`${base}/export/`, { params: p, responseType: 'blob' })
