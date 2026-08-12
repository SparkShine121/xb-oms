import request from './request'
export const login = (d: { username: string; password: string }) => request.post('/auth/login/', d)
export const me = () => request.get('/auth/me/')
