import axios from 'axios'
import router from '@/router'
// 환경변수에서 API URL 가져오기 (Railway 백엔드)
// 개발 환경: /api (Vite 프록시)
// 프로덕션: VITE_API_URL (Railway URL)
const baseURL = import.meta.env.VITE_API_URL 
  ? `${import.meta.env.VITE_API_URL}/api`
  : '/api'

// 환경변수에서 API URL 가져오기 (Render 백엔드)
// 개발 환경: /api (Vite 프록시)
// 프로덕션: VITE_API_URL (Render URL)
const baseURL = import.meta.env.VITE_API_URL 
  ? `${import.meta.env.VITE_API_URL}/api`
  : '/api'

const api = axios.create({
  baseURL,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json'
  }
})










api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      router.push({ name: 'Login' })
    }
    return Promise.reject(error)
  }
)

export default api
