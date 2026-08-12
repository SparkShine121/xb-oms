import request from './request'
const base = '/basic-info'
export const listCategories = (p?: any) => request.get(`${base}/categories/`, { params: p })
export const createCategory = (d: any) => request.post(`${base}/categories/`, d)
export const updateCategory = (id: number, d: any) => request.patch(`${base}/categories/${id}/`, d)
export const deleteCategory = (id: number) => request.delete(`${base}/categories/${id}/`)
export const categoryTree = () => request.get(`${base}/categories/tree/`)
export const listProducts = (p?: any) => request.get(`${base}/products/`, { params: p })
export const createProduct = (d: any) => request.post(`${base}/products/`, d)
export const updateProduct = (id: number, d: any) => request.patch(`${base}/products/${id}/`, d)
export const deleteProduct = (id: number) => request.delete(`${base}/products/${id}/`)
export const importProducts = (file: File) => { const fd = new FormData(); fd.append('file', file); return request.post(`${base}/products/import/`, fd, { headers: { 'Content-Type': 'multipart/form-data' } }) }
export const downloadProductTemplate = () => request.get(`${base}/products/import-template/`, { responseType: 'blob' })
// Factory / Logistics / Customer 同模式（list/create/update/delete + factory import/template）
export const listFactories = (p?: any) => request.get(`${base}/factories/`, { params: p })
export const createFactory = (d: any) => request.post(`${base}/factories/`, d)
export const updateFactory = (id: number, d: any) => request.patch(`${base}/factories/${id}/`, d)
export const deleteFactory = (id: number) => request.delete(`${base}/factories/${id}/`)
export const importFactories = (file: File) => { const fd = new FormData(); fd.append('file', file); return request.post(`${base}/factories/import/`, fd, { headers: { 'Content-Type': 'multipart/form-data' } }) }
export const downloadFactoryTemplate = () => request.get(`${base}/factories/import-template/`, { responseType: 'blob' })
export const listLogistics = (p?: any) => request.get(`${base}/logistics/`, { params: p })
export const createLogistics = (d: any) => request.post(`${base}/logistics/`, d)
export const updateLogistics = (id: number, d: any) => request.patch(`${base}/logistics/${id}/`, d)
export const deleteLogistics = (id: number) => request.delete(`${base}/logistics/${id}/`)
export const listCustomers = (p?: any) => request.get(`${base}/customers/`, { params: p })
export const createCustomer = (d: any) => request.post(`${base}/customers/`, d)
export const updateCustomer = (id: number, d: any) => request.patch(`${base}/customers/${id}/`, d)
export const deleteCustomer = (id: number) => request.delete(`${base}/customers/${id}/`)
