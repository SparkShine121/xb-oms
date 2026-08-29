import request from './request'
const base = '/logistics'

export const listShipments = (p?: any) =>
  request.get(`${base}/shipments/`, { params: p })
export const getShipment = (id: number) =>
  request.get(`${base}/shipments/${id}/`)
export const createShipment = (d: any) =>
  request.post(`${base}/shipments/`, d)
export const updateShipment = (id: number, d: any) =>
  request.patch(`${base}/shipments/${id}/`, d)
export const deleteShipment = (id: number) =>
  request.delete(`${base}/shipments/${id}/`)
export const bulkDeleteShipments = (ids: number[]) =>
  request.post(`${base}/shipments/bulk-delete/`, { ids })
