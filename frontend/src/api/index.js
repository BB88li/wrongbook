import axios from 'axios'
import { ElMessage } from 'element-plus'

// 开发环境后端在 8000 端口；Vite 代理见 vite.config.js
const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
})

// 统一错误提示：后端 4xx/5xx 时不再静默失败。
// FastAPI 的 422 校验错误 detail 是数组，这里取 msg 拼起来。
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const detail = error.response?.data?.detail
    const message = Array.isArray(detail)
      ? detail.map((item) => item.msg || String(item)).join('；')
      : detail || error.message || '请求失败'
    ElMessage.error(message)
    return Promise.reject(error)
  },
)

export const mistakeApi = {
  list: (subject) => api.get('/mistakes', { params: { subject } }),
  get: (id) => api.get(`/mistakes/${id}`),
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

export const settingsApi = {
  get: () => api.get('/settings'),
  update: (data) => api.put('/settings', data),
}

export default api
