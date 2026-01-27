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

// 响应拦截器 - 处理错误
service.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    console.error('Request Error:', error)

    // 处理不同的错误状态码
    if (error.response) {
      const status = error.response.status
      const message = error.response.data?.detail || error.response.data?.message
      const url = error.config?.url || ''

      switch (status) {
        case 401:
          // 区分登录失败和 Token 过期
          if (url.includes('/auth/login')) {
            // 登录接口返回 401，说明用户名或密码错误
            ElMessage.error(message || '用户名或密码错误')
          } else {
            // 其他接口返回 401，说明 Token 过期
            removeToken()
            ElMessage.error('登录已过期,请重新登录')
            // 使用 router 跳转而不是 window.location
            setTimeout(() => {
              window.location.href = '/login'
            }, 1000)
          }
          break
        case 400:
          ElMessage.error(message || '请求参数错误')
          break
        case 404:
          ElMessage.error('请求的资源不存在')
          break
        case 500:
          ElMessage.error('服务器错误,请稍后重试')
          break
        default:
          ElMessage.error(message || '请求失败')
      }
    } else if (error.request) {
      // 请求已发出但没有收到响应
      ElMessage.error('网络错误,请检查网络连接')
    } else {
      // 其他错误
      ElMessage.error('请求失败: ' + error.message)
    }

    return Promise.reject(error)
  }
)

export default service
