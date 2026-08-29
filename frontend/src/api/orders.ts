import request from './request'
const base = '/orders'
export const listOrders = (p?: any) => request.get(`${base}/orders/`, { params: p })
export const getOrder = (id: number) => request.get(`${base}/orders/${id}/`)
export const createOrder = (d: any) => request.post(`${base}/orders/`, d)
export const updateOrder = (id: number, d: any) => request.patch(`${base}/orders/${id}/`, d)
export const deleteOrder = (id: number) => request.delete(`${base}/orders/${id}/`)
export const bulkDeleteOrders = (ids: number[]) => request.post(`${base}/orders/bulk-delete/`, { ids })
export const importOrders = (file: File) => { const fd = new FormData(); fd.append('file', file); return request.post(`${base}/orders/import/`, fd, { headers: { 'Content-Type': 'multipart/form-data' } }) }
export const downloadOrderTemplate = () => request.get(`${base}/orders/import-template/`, { responseType: 'blob' })
export const setTracker = (id: number, tracker: number) => request.post(`${base}/orders/${id}/set-tracker/`, { tracker })
export const listExchangeRates = (p?: any) => request.get(`${base}/exchange-rates/`, { params: p })
export const createExchangeRate = (d: any) => request.post(`${base}/exchange-rates/`, d)
export const updateExchangeRate = (id: number, d: any) => request.patch(`${base}/exchange-rates/${id}/`, d)
export const deleteExchangeRate = (id: number) => request.delete(`${base}/exchange-rates/${id}/`)