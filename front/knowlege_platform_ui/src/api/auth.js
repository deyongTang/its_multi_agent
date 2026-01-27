import request from './request'

/**
 * 用户登录
 * @param {Object} data - 登录信息
 * @param {string} data.username - 用户名
 * @param {string} data.password - 密码
 * @returns {Promise} 返回 access_token 和 refresh_token
 */
export function login(data) {
  return request({
    url: '/auth/login',
    method: 'post',
    data
  })
}

/**
 * 刷新 Token
 * @param {string} refreshToken - Refresh Token
 * @returns {Promise} 返回新的 tokens
 */
export function refreshToken(refreshToken) {
  return request({
    url: '/auth/refresh',
    method: 'post',
    data: { refresh_token: refreshToken }
  })
}

/**
 * 获取当前用户信息
 * @returns {Promise} 返回用户信息
 */
export function getCurrentUser() {
  return request({
    url: '/auth/me',
    method: 'get'
  })
}
