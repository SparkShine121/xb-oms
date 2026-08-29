import request from './request'
const base = '/factory-payment'

export const listPayments = (p?: any) =>
  request.get(`${base}/payments/`, { params: p })
export const getPayment = (id: number) =>
  request.get(`${base}/payments/${id}/`)
export const createPayment = (d: any) =>
  request.post(`${base}/payments/`, d)
export const updatePayment = (id: number, d: any) =>
  request.patch(`${base}/payments/${id}/`, d)
export const deletePayment = (id: number) =>
  request.delete(`${base}/payments/${id}/`)
export const bulkDeletePayments = (ids: number[]) =>
  request.post(`${base}/payments/bulk-delete/`, { ids })

export const listRecords = (p?: any) =>
  request.get(`${base}/records/`, { params: p })
export const createRecord = (d: any) =>
  request.post(`${base}/records/`, d)
export const deleteRecord = (id: number) =>
  request.delete(`${base}/records/${id}/`)

export const generateByOrder = (orderId: number) =>
  request.post(`${base}/payments/orders/${orderId}/generate/`)

export const getStatement = (p?: any) =>
  request.get(`${base}/payments/statement/`, { params: p })
