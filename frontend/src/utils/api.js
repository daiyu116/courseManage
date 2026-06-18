// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2024-2026 CourseArrange Contributors
import axios from 'axios'
import { ElMessage } from 'element-plus'

let errorMessageQueue = []
let errorTimer = null

function showError(message) {
  errorMessageQueue.push(message)
  
  if (errorTimer) {
    clearTimeout(errorTimer)
  }
  
  errorTimer = setTimeout(() => {
    if (errorMessageQueue.length > 0) {
      const uniqueMessages = [...new Set(errorMessageQueue)]
      if (uniqueMessages.length === 1) {
        ElMessage.error(uniqueMessages[0])
      } else {
        ElMessage.error(`发生 ${uniqueMessages.length} 个错误，请检查网络连接`)
      }
      errorMessageQueue = []
    }
    errorTimer = null
  }, 500)
}

function isTokenExpiringSoon() {
  const token = localStorage.getItem('token')
  if (!token) return false
  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    if (!payload.exp) return false
    const expiresAt = payload.exp * 1000
    const now = Date.now()
    const remaining = expiresAt - now
    const TOKEN_REFRESH_THRESHOLD = 10 * 60 * 1000
    return remaining > 0 && remaining < TOKEN_REFRESH_THRESHOLD
  } catch {
    return false
  }
}

let refreshPromise = null

async function refreshTokenIfNeeded() {
  if (!isTokenExpiringSoon()) return
  if (refreshPromise) return refreshPromise

  refreshPromise = axios.post('/api/auth/refresh', null, {
    headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
  }).then(response => {
    const newToken = response.data.access_token
    if (newToken) {
      localStorage.setItem('token', newToken)
    }
    refreshPromise = null
  }).catch(() => {
    refreshPromise = null
  })

  return refreshPromise
}

const api = axios.create({
  baseURL: '/api',
  timeout: 30000
})

api.interceptors.request.use(
  async config => {
    const token = localStorage.getItem('token')
    if (token) {
      await refreshTokenIfNeeded()
      config.headers.Authorization = `Bearer ${localStorage.getItem('token')}`
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

api.interceptors.response.use(
  response => {
    return response
  },
  error => {
    if (error.response) {
      const { status, data } = error.response
      if (status === 401) {
        const currentPath = window.location.pathname
        const isLoginPage = currentPath === '/admin/login'
        
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        
        if (!isLoginPage && currentPath.startsWith('/admin')) {
          ElMessage.error('登录已过期，请重新登录')
          setTimeout(() => {
            window.location.href = '/admin/login'
          }, 300)
        }
      } else if (status === 403) {
        showError('权限不足，需要管理员权限')
      } else {
        showError(data.detail || '请求失败')
      }
    } else if (error.code === 'ECONNABORTED') {
      showError('请求超时，请检查网络连接')
    } else {
      showError('网络错误')
    }
    return Promise.reject(error)
  }
)

export default api