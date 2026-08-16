import request from './request'
const base = '/tracking'
export const listMyOrders = (p?: any) => request.get(`${base}/my/`, { params: p })
export const advanceOrder = (id: number, data: { note: string; photos?: File[] }) => {
  const fd = new FormData()
  fd.append('note', data.note)
  ;(data.photos || []).forEach(p => fd.append('photos', p))
  return request.post(`${base}/orders/${id}/advance/`, fd, { headers: { 'Content-Type': 'multipart/form-data' } })
}
export const rejectOrder = (id: number, data: { note: string; photos?: File[] }) => {
  const fd = new FormData()
  fd.append('note', data.note)
  ;(data.photos || []).forEach(p => fd.append('photos', p))
  return request.post(`${base}/orders/${id}/reject/`, fd, { headers: { 'Content-Type': 'multipart/form-data' } })
}
export const getTimeline = (id: number) => request.get(`${base}/orders/${id}/timeline/`)
