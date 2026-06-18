// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2024-2026 courseManage Contributors
<template>
  <div class="login-container">
    <el-card class="login-card">
      <template #header>
        <div class="card-header">
          <h2>后台管理系统登录</h2>
        </div>
      </template>
      <el-form :model="loginForm" :rules="rules" ref="loginFormRef" label-width="80px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="loginForm.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="loginForm.password" type="password" placeholder="请输入密码" @keyup.enter="handleLogin" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleLogin" :loading="loading" style="width: 100%">
            登录
          </el-button>
          <div style="display: flex; justify-content: space-between; width: 100%; margin-top: 10px;">
            <el-button link @click="showForgotPasswordDialog">忘记密码？</el-button>
            <el-tooltip :content="openRegistrationEnabled ? '点击注册新账户' : '开放注册未启用，请联系管理员开启'" placement="top">
              <el-button link :type="openRegistrationEnabled ? 'success' : 'info'" :disabled="!openRegistrationEnabled" @click="showRegisterDialog">注册新账户</el-button>
            </el-tooltip>
          </div>
        </el-form-item>
      </el-form>
      <div class="default-account-hint">
        <el-divider content-position="center">首次登录</el-divider>
        <p>默认账号：<strong>admin</strong> / <strong>admin123</strong></p>
        <p>登录后请立即修改密码</p>
      </div>
    </el-card>
    <!-- 忘记密码对话框 -->
    <el-dialog v-model="forgotPasswordDialogVisible" title="忘记密码" width="400px">
        <el-form :model="forgotPasswordForm" :rules="forgotPasswordRules" ref="forgotPasswordFormRef" label-width="80px">
            <el-form-item label="用户名" prop="username">
            <el-input v-model="forgotPasswordForm.username" placeholder="请输入用户名" />
            </el-form-item>
        </el-form>
        <template #footer>
            <el-button @click="forgotPasswordDialogVisible = false">取消</el-button>
            <el-button type="primary" @click="handleForgotPassword">确认忘记</el-button>
        </template>
    </el-dialog>
    <!-- 注册对话框 -->
    <el-dialog v-model="registerDialogVisible" title="注册新账户" width="450px" :close-on-click-modal="false">
      <el-alert
        type="warning"
        :closable="false"
        style="margin-bottom: 15px;"
      >
        <template #title>
          <span style="font-size: 13px;">开放注册为临时功能，注册后默认角色为<strong>课程管理员</strong>，请填写真实邮箱以接收确认邮件。</span>
        </template>
      </el-alert>
      <el-form :model="registerForm" :rules="registerRules" ref="registerFormRef" label-width="80px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="registerForm.username" placeholder="请输入用户名（2-50个字符）" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="registerForm.email" placeholder="请输入邮箱地址" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="registerForm.password" type="password" show-password placeholder="请输入密码（至少6位）" />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input v-model="registerForm.confirmPassword" type="password" show-password placeholder="请再次输入密码" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="registerDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleRegister" :loading="registerLoading">提交注册</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/utils/api'

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
      console.error('[OpenRegistration] API响应异常:', response.status)
      openRegistrationEnabled.value = false
      return
    }
    const data = await response.json()
    openRegistrationEnabled.value = data.enabled
    console.log('[OpenRegistration] API响应:', response.status, data)
  } catch (error) {
    openRegistrationEnabled.value = false
    console.error('[OpenRegistration] API调用失败:', error)
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
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
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
          window.logger.error('获取站点配置失败:', error)
        }

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
        ElMessage.success('登录成功')
        if (response.data.must_change_password) {
          ElMessage.warning('检测到您使用的是默认密码，请立即修改密码！')
          router.push('/admin/dashboard?force_change_password=1')
        } else {
          router.push('/admin/dashboard')
        }
      } catch (error) {
        window.logger.error('登录失败:', error)
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
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }]
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
          `确认忘记密码？我们将向管理员发送重置请求，请等待管理员处理。`,
          '提示',
          {
            confirmButtonText: '确认',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )
        
        await api.post('/auth/forgot-password', forgotPasswordForm.value)
        ElMessage.success('密码重置请求已发送，请等待管理员处理')
        forgotPasswordDialogVisible.value = false
        forgotPasswordForm.value = { username: '' }
      } catch (error) {
        if (error !== 'cancel') {
          window.logger.error('发送密码重置请求失败:', error)
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
    callback(new Error('请再次输入密码'))
  } else if (value !== registerForm.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const registerRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 2, max: 50, message: '用户名长度为2-50个字符', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
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
        ElMessage.success('注册申请已提交！请查收邮箱确认邮件完成注册。')
        registerDialogVisible.value = false
      } catch (error) {
        window.logger.error('注册失败:', error)
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