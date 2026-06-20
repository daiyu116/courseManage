import axios from 'axios'
import { ElMessage } from 'element-plus'
import i18n from '@/locales'

const { t } = i18n.global

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
        ElMessage.error(t('api.multipleErrors', { n: uniqueMessages.length }))
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
          ElMessage.error(t('api.loginExpired'))
          setTimeout(() => {
            window.location.href = '/admin/login'
          }, 300)
        }
      } else if (status === 403) {
        showError(t('api.permissionDenied'))
      } else {
        showError(data.detail || t('api.requestFailed'))
      }
    } else if (error.code === 'ECONNABORTED') {
      showError(t('api.requestTimeout'))
    } else {
      showError(t('api.networkError'))
    }
    return Promise.reject(error)
  }
)

export default api