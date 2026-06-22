// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2024-2026 courseManage Contributors
<template>
  <div class="login-container">
    <el-card class="login-card">
      <template #header>
        <div class="card-header">
          <h2>{{ t('login.title') }}</h2>
        </div>
      </template>
      <el-form :model="loginForm" :rules="rules" ref="loginFormRef" label-width="80px">
        <el-form-item :label="t('login.username')" prop="username">
          <el-input v-model="loginForm.username" :placeholder="t('login.usernamePlaceholder')" />
        </el-form-item>
        <el-form-item :label="t('login.password')" prop="password">
          <el-input v-model="loginForm.password" type="password" :placeholder="t('login.passwordPlaceholder')" @keyup.enter="handleLogin" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleLogin" :loading="loading" style="width: 100%">
            {{ t('login.loginButton') }}
          </el-button>
          <div style="display: flex; justify-content: space-between; width: 100%; margin-top: 10px;">
            <el-button link @click="showForgotPasswordDialog">{{ t('login.forgotPassword') }}</el-button>
            <el-tooltip :content="openRegistrationEnabled ? t('login.registerTooltipEnabled') : t('login.registerTooltipDisabled')" placement="top">
              <el-button link :type="openRegistrationEnabled ? 'success' : 'info'" :disabled="!openRegistrationEnabled" @click="showRegisterDialog">{{ t('login.registerNew') }}</el-button>
            </el-tooltip>
          </div>
        </el-form-item>
      </el-form>
      <div class="default-account-hint">
        <el-divider content-position="center">{{ t('login.firstLogin') }}</el-divider>
        <p>{{ t('login.defaultAccount') }}<strong>admin</strong> / <strong>Admin.123</strong></p>
        <p>{{ t('login.changePasswordAfterLogin') }}</p>
      </div>
    </el-card>
    <el-dialog v-model="forgotPasswordDialogVisible" :title="t('login.forgotPasswordTitle')" width="400px">
        <el-form :model="forgotPasswordForm" :rules="forgotPasswordRules" ref="forgotPasswordFormRef" label-width="80px">
            <el-form-item :label="t('login.username')" prop="username">
            <el-input v-model="forgotPasswordForm.username" :placeholder="t('login.usernamePlaceholder')" />
            </el-form-item>
        </el-form>
        <template #footer>
            <el-button @click="forgotPasswordDialogVisible = false">{{ t('common.cancel') }}</el-button>
            <el-button type="primary" @click="handleForgotPassword">{{ t('login.forgotPasswordConfirm') }}</el-button>
        </template>
    </el-dialog>
    <el-dialog v-model="registerDialogVisible" :title="t('login.registerTitle')" width="450px" :close-on-click-modal="false">
      <el-alert
        type="warning"
        :closable="false"
        style="margin-bottom: 15px;"
      >
        <template #title>
          <span style="font-size: 13px;">{{ t('login.registerWarning') }}</span>
        </template>
      </el-alert>
      <el-form :model="registerForm" :rules="registerRules" ref="registerFormRef" label-width="80px">
        <el-form-item :label="t('login.username')" prop="username">
          <el-input v-model="registerForm.username" :placeholder="t('login.usernamePlaceholder2')" />
        </el-form-item>
        <el-form-item :label="t('login.email')" prop="email">
          <el-input v-model="registerForm.email" :placeholder="t('login.emailPlaceholder')" />
        </el-form-item>
        <el-form-item :label="t('login.password')" prop="password">
          <el-input v-model="registerForm.password" type="password" show-password :placeholder="t('login.passwordPlaceholder2')" />
        </el-form-item>
        <el-form-item :label="t('login.confirmPassword')" prop="confirmPassword">
          <el-input v-model="registerForm.confirmPassword" type="password" show-password :placeholder="t('login.confirmPasswordPlaceholder')" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="registerDialogVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleRegister" :loading="registerLoading">{{ t('login.registerSubmit') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useI18n } from 'vue-i18n'
import api from '@/utils/api'
import { loadLicenseStatus } from '@/utils/license'

const { t } = useI18n()
const router = useRouter()
const loginFormRef = ref(null)
const loading = ref(false)

const openRegistrationEnabled = ref(false)

const checkOpenRegistration = async () => {
  try {
    const response = await fetch('/api/public/open-registration-status', {
      credentials: 'omit',
      headers: { 'Cache-Control': 'no-cache' }
    })
    if (!response.ok) {
      console.error('[OpenRegistration] API response error:', response.status)
      openRegistrationEnabled.value = false
      return
    }
    const data = await response.json()
    openRegistrationEnabled.value = data.enabled
  } catch (error) {
    openRegistrationEnabled.value = false
    console.error('[OpenRegistration] API call failed:', error)
  }
}

onMounted(() => {
  checkOpenRegistration()
})

const loginForm = reactive({
  username: '',
  password: ''
})

const rules = {
  username: [{ required: true, message: () => t('login.usernameRequired'), trigger: 'blur' }],
  password: [{ required: true, message: () => t('login.passwordRequired'), trigger: 'blur' }]
}

const handleLogin = async () => {
  if (!loginFormRef.value) return
  
  await loginFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        const formData = new FormData()
        formData.append('username', loginForm.username)
        formData.append('password', loginForm.password)
        
        const response = await api.post('/auth/login', formData, {
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
          }
        })
        
        localStorage.setItem('token', response.data.access_token)
        localStorage.setItem('user', JSON.stringify({ 
          id: response.data.user.id,
          username: loginForm.username,
          teacher_id: response.data.user.teacher_id,
          role: response.data.user.role,
          is_admin: response.data.is_admin,
          is_subject_teacher: response.data.is_subject_teacher || false,
          must_change_password: response.data.must_change_password || false
        }))

        try {
          const settingsResponse = await api.get('/settings')
          if (settingsResponse.data && settingsResponse.data.subject_teachers) {
            localStorage.setItem('subject_teachers', JSON.stringify(settingsResponse.data.subject_teachers))
          }
          if (settingsResponse.data && settingsResponse.data.fee_managers) {
            localStorage.setItem('fee_managers', JSON.stringify(settingsResponse.data.fee_managers))
          }
          if (settingsResponse.data && settingsResponse.data.grade_managers) {
            localStorage.setItem('grade_managers', JSON.stringify(settingsResponse.data.grade_managers))
          }
          if (settingsResponse.data && settingsResponse.data.operation_managers) {
            localStorage.setItem('operation_managers', JSON.stringify(settingsResponse.data.operation_managers))
          }
        } catch (error) {
          window.logger.error('Failed to load site settings:', error)
        }

        await loadLicenseStatus()

        window.dispatchEvent(new CustomEvent('user-logged-in', { 
          detail: { 
            id: response.data.user.id,
            username: loginForm.username,
            role: response.data.user.role,
            teacher_id: response.data.user.teacher_id,
            is_admin: response.data.is_admin,
            is_subject_teacher: response.data.is_subject_teacher || false
          } 
        }))
        ElMessage.success(t('login.loginSuccess'))
        if (response.data.must_change_password) {
          ElMessage.warning(t('login.mustChangePassword'))
          router.push('/admin/dashboard?force_change_password=1')
        } else {
          router.push('/admin/dashboard')
        }
      } catch (error) {
        window.logger.error('Login failed:', error)
      } finally {
        loading.value = false
      }
    }
  })
}

const forgotPasswordDialogVisible = ref(false)
const forgotPasswordForm = ref({
  username: ''
})
const forgotPasswordFormRef = ref(null)

const forgotPasswordRules = {
  username: [{ required: true, message: () => t('login.usernameRequired'), trigger: 'blur' }]
}

const showForgotPasswordDialog = () => {
  forgotPasswordDialogVisible.value = true
}

const handleForgotPassword = async () => {
  if (!forgotPasswordFormRef.value) return
  
  await forgotPasswordFormRef.value.validate(async (valid) => {
    if (valid) {
      try {
        await ElMessageBox.confirm(
          t('login.forgotPasswordConfirm'),
          t('common.tip'),
          {
            confirmButtonText: t('common.confirm'),
            cancelButtonText: t('common.cancel'),
            type: 'warning'
          }
        )
        
        await api.post('/auth/forgot-password', forgotPasswordForm.value)
        ElMessage.success(t('login.forgotPasswordSuccess'))
        forgotPasswordDialogVisible.value = false
        forgotPasswordForm.value = { username: '' }
      } catch (error) {
        if (error !== 'cancel') {
          window.logger.error('Failed to send password reset request:', error)
        }
      }
    }
  })
}

const registerDialogVisible = ref(false)
const registerLoading = ref(false)
const registerFormRef = ref(null)
const registerForm = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: ''
})

const validateConfirmPassword = (rule, value, callback) => {
  if (value === '') {
    callback(new Error(t('login.confirmPasswordRequired')))
  } else if (value !== registerForm.password) {
    callback(new Error(t('login.passwordMismatch')))
  } else {
    callback()
  }
}

const registerRules = {
  username: [
    { required: true, message: () => t('login.usernameRequired'), trigger: 'blur' },
    { min: 2, max: 50, message: () => t('login.usernameLength'), trigger: 'blur' }
  ],
  email: [
    { required: true, message: () => t('login.emailRequired'), trigger: 'blur' },
    { type: 'email', message: () => t('login.emailInvalid'), trigger: 'blur' }
  ],
  password: [
    { required: true, message: () => t('login.passwordRequired'), trigger: 'blur' },
    { min: 6, message: () => t('login.passwordMin'), trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

const showRegisterDialog = () => {
  registerForm.username = ''
  registerForm.email = ''
  registerForm.password = ''
  registerForm.confirmPassword = ''
  registerDialogVisible.value = true
}

const handleRegister = async () => {
  if (!registerFormRef.value) return
  
  await registerFormRef.value.validate(async (valid) => {
    if (valid) {
      registerLoading.value = true
      try {
        await api.post('/auth/open-register', {
          username: registerForm.username,
          email: registerForm.email,
          password: registerForm.password
        })
        ElMessage.success(t('login.registerSuccess'))
        registerDialogVisible.value = false
      } catch (error) {
        window.logger.error('Registration failed:', error)
      } finally {
        registerLoading.value = false
      }
    }
  })
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 80vh;
}

.login-card {
  width: 400px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.card-header {
  text-align: center;
}

.card-header h2 {
  margin: 0;
  color: #333;
}

.default-account-hint {
  text-align: center;
  color: #909399;
  font-size: 13px;
  line-height: 1.8;
}

.default-account-hint p {
  margin: 0;
}

.default-account-hint strong {
  color: #409eff;
}
</style>