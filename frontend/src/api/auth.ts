import request from './request'
export const login = (d: { username: string; password: string }) => request.post('/auth/login/', d)
export const me = () => request.get('/auth/me/')
// Task 14: 用户管理（admin 专属）
export const listUsers = (p?: any) => request.get('/auth/users/', { params: p })
export const createUser = (d: any) => request.post('/auth/users/', d)
export const updateUser = (id: number, d: any) => request.patch(`/auth/users/${id}/`, d)
export const deleteUser = (id: number) => request.delete(`/auth/users/${id}/`)
