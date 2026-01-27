import axios from 'axios'
import { getToken, removeToken } from '@/utils/auth'
import { ElMessage } from 'element-plus'

const service = axios.create({
  baseURL: '/api',
  timeout: 50000
})

// 请求拦截器 - 添加 Token
service.interceptors.request.use(
  config => {
    const token = getToken()
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`
    }
    return config
  },
  error => {
    console.error('Request Error:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器 - 处理 Token 过期
service.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    if (error.response?.status === 401) {
      removeToken()
      ElMessage.error('登录已过期,请重新登录')
      window.location.href = '/login'
    } else {
      console.error('Request Error:', error)
    }
    return Promise.reject(error)
  }
)

export default service
