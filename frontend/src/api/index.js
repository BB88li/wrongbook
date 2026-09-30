import axios from 'axios'

// 开发环境后端在 8000 端口；Vite 代理见 vite.config.js
const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
})

export const mistakeApi = {
  list: (subject) => api.get('/mistakes', { params: { subject } }),
  create: (data) => api.post('/mistakes', data),
  update: (id, data) => api.put(`/mistakes/${id}`, data),
  remove: (id) => api.delete(`/mistakes/${id}`),
}

export const reviewApi = {
  due: () => api.get('/reviews/due'),
  submit: (data) => api.post('/reviews', data),
}

export const knowledgeApi = {
  list: () => api.get('/knowledge-points'),
}

export default api
